#!/usr/bin/env python3

import sys
import argparse
from pydfa.dfa_analysis import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='DFA simulation: ECDSA and multiplicative splitting')
        
    try:
        parser.add_argument('--curve', action='store', dest='curve_name', type=str,
                            help=f'Choose amongst: {CURVES.keys()}', required=True)
                
        parser.add_argument('--skip', action='store', dest='skip', type=int,
                            help='Step where the fault occurs', required=True)
        
        parser.add_argument('--lambda', action='store', dest='llambda', type=int,
                            help='Size of random parameters in bits', required=True)
        
        parser.add_argument('--nsig', action='store', dest='nsig', type=int,
                            help='Number of signatures to attack')
        
        parser.add_argument('--fname', action='store', dest='fname', type=str,
                            help='To the results of analysis for use with HNP solver', required=True)
    
        args = parser.parse_args()

        curve = CurveJac(CURVES[args.curve_name])

        # key pair generation
        privkey, pubkey = generate_keypair(curve)
        print(f'Key pair generated on curve {curve.name}:')
        print(f'    Private key: {privkey}')
        print(f'    Public key : ({pubkey[0].hex()},')
        print(f'                  {pubkey[1].hex()})')
              
        # simulate "nsig" ECDSA signatures with a fault
        print(f'Generating {args.nsig} signatures')
        list_sig = simulation_ecdsa(curve, privkey, 'multsplit', args.nsig, args.skip, args.llambda)

        # DFA analysis
        print(f'DFA analysis on the signatures')
        Ui, Vi, Li = batch_analysis_ecdsa_multsplit(curve, pubkey, list_sig, args.skip, args.llambda)
        n = len(Ui)
        print(f'Number of invalid signatures: {n}')
        print(f'Expect at least {(curve.order.bit_length() + args.skip - 1)//(args.skip)} signatures for HNP to succeed')
        
        f = open(args.fname, 'w')        
        # We only keep the curve name and the public key
        f.write(f'{curve.name},{pubkey[0].hex()},{pubkey[1].hex()}\n')
        for u,v,L in zip(Ui,Vi,Li):
            f.write(f'{u:x},{v:x},{L}\n')
        f.close()

        print(f'The results of the analysis are stored in {args.fname}')

    except Exception as e:
        print(e)

