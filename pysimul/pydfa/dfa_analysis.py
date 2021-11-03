#!/usr/bin/env python3

from pydfa.ec import *
from pydfa.dfa_dl import bsgs

def simulation_ecdsa(curve, privkey, scalar_mult_mode, nsig, skip=-1, llambda=20):
    '''Generates `nsig` signatures according to `scalar_mult_mode` with optional fault'''

    ecsm_func = SCALAR_MULT_MODE[scalar_mult_mode]
    list_sig = []
    for i in range(nsig):
        # We sign a random message
        msg = randint(1, curve.order - 1)
        r, s = ecdsa_sign(curve, privkey, msg, ecsm_func, skip, llambda)
        list_sig.append((msg,r,s))

    return list_sig


## normal method (padding only)

def dfa_swap_analysis(curve, Q, QQ, skip):
    '''Returns candidate for lsb of scalar if found'''
    
    if Q == QQ:
        return False, 0

    QQ = curve.neg(QQ)

    # diff = Q - Q' + [2^skip]*P = [2*(k mod 2^skip)]*P 
    diff = curve.add_aff(Q, QQ)
    tmp = curve.ladder(2**skip, curve.base)
    diff = curve.add_aff(diff, tmp)
    
    try:
        if diff == curve.infty:
            dl = 0
        else:
            dl = bsgs(curve, diff, curve.base, bounds=(0,2**(skip + 1)))
        found = True
            
    except Exception as e:
        dl = 0
        found = False

    return found, dl//2


def dfa_leak_from_sig(curve, pubkey, msg, sig, skip):
    '''Returns validity of signature and list of potential candidates for lsb of the nonce'''

    valid, Q, QQ_list = points_from_sig(curve, pubkey, msg, sig)
    leak = []
    for QQ in QQ_list:
        found, lsb = dfa_swap_analysis(curve, Q, QQ, skip)
        if found:
            leak.append(lsb)

    return valid, leak


def batch_analysis_ecdsa_normal(curve, pubkey, list_sig, skip):
    '''DFA analysis of list of signatures and prepare file for HNP'''
    
    Ui, Vi, Li = [], [], []
    for i in range(len(list_sig)):
        msg, r, s = list_sig[i]
        valid, leak = dfa_leak_from_sig(curve, pubkey, msg, (r,s), skip)
        
        if valid:
            print(f'Signature {i + 1}/{len(list_sig)}: valid')
            continue

        if len(leak) != 1:
            print(f'Signature {i + 1}/{len(list_sig)}: number of solutions is {len(leak)}') 
            continue

        lsb = leak[0]        
        print(f'Signature {i + 1}/{len(list_sig)}: padded nonce mod 2**{skip} = {lsb}')

        B1 = (2**curve.order.bit_length() - lsb + 1) >> skip
        B2 = (2**curve.order.bit_length() + curve.order - lsb) >> skip

        C = (B1 + B2)//2
        LL = curve.order//(B2 - B1)

        tmp = invmod(s*2**skip, curve.order)
        u = r*tmp % curve.order
        v = (msg - s*lsb)*tmp % curve.order
        vv = C - v

        Ui.append(u)
        Vi.append(vv)
        Li.append(LL)

    return Ui, Vi, Li


## group order blinding

def batch_analysis_ecdsa_blinding(curve, pubkey, list_sig, skip, llambda):
    '''DFA analysis of list of signatures and prepare file for HNP (with nonce blinding by Coron 1st countermeeasure)'''

    Ui, Vi, Li = [], [], []
    for i in range(len(list_sig)):
        msg, r, s = list_sig[i]
        valid, leak = dfa_leak_from_sig(curve, pubkey, msg, (r,s), skip)

        if valid:
            print(f'Signature {i + 1}/{len(list_sig)}: valid')
            continue

        if len(leak) != 1:
            print(f'Signature {i + 1}/{len(list_sig)}: number of solutions is {len(leak)}') 
            continue

        lsb = leak[0]        
        print(f'Signature {i + 1}/{len(list_sig)}: blinded nonce mod 2**{skip} = {lsb}')

        B1 = (curve.order - lsb + 1) >> skip
        B2 = (curve.order*(2**llambda + 1) - lsb) >> skip

        C = (B1 + B2)//2
        LL = curve.order//(B2 - B1)

        tmp = invmod(s*2**skip, curve.order)
        u = r*tmp % curve.order
        v = (msg - s*lsb)*tmp % curve.order
        vv = C - v

        Ui.append(u)
        Vi.append(vv)
        Li.append(LL)

    return Ui, Vi, Li


## Euclidean splitting

def dfa_swap_analysis_euclsplit(curve, Q, QQ, skip, llambda):
    '''Returns candidates (m,b) such that k mod m = b and Q = [k]*P'''

    res = []
 
    # baby steps
    b = 0
    baby = curve.infty
    table = dict()
    table[baby] = 0
    for b in range(1, 2**llambda):
        baby = curve.add_aff(baby, curve.base)
        table[baby] = b
    
    # giant steps
    # m = m1*2**skip + m0
    QQ = curve.neg(QQ)
    diff = curve.add_aff(Q, QQ)
    
    for m0 in range(2**skip):
        if m0 == 2**(skip - 1): continue
        tmp = invmod(2*m0 - 2**skip, curve.order)
        R = curve.ladder(tmp, diff)
        giantstep = curve.ladder(2**skip, R)
        giantstep = curve.neg(giantstep)
        giant = curve.ladder(2**(llambda - 1) + m0, R)
        giant = curve.neg(giant)
        giant = curve.add_aff(Q, giant)

        for m1 in range(2**(llambda - skip - 1), 2**(llambda - skip)):
            b = table.get(giant)
            if b is not None:
                m = m1*2**skip + m0
                res.append((m, b))
            giant = curve.add_aff(giant, giantstep)

    return res


def dfa_leak_from_sig_euclsplit(curve, pubkey, msg, sig, skip, llambda):
    '''Returns validity of signature and list of potential leak candidates on the nonce'''
    
    valid, Q, QQ_list = points_from_sig(curve, pubkey, msg, sig)
    for QQ in QQ_list:
        leak = dfa_swap_analysis_euclsplit(curve, Q, QQ, skip, llambda)
        if len(leak) > 0:
            return valid, leak
    return valid, []


def batch_analysis_ecdsa_euclsplit(curve, pubkey, list_sig, skip, llambda):
    '''DFA analysis of list of signatures and prepare file for HNP (with Eucl. splitting of the nonce countermeeasure)'''

    Ui, Vi, Li = [], [], []
    for i in range(len(list_sig)):
        msg, r, s = list_sig[i]
        valid, leak = dfa_leak_from_sig_euclsplit(curve, pubkey, msg, (r,s), skip, llambda)

        if valid:
            print(f'Signature {i + 1}/{len(list_sig)}: valid')
            continue
            
        if len(leak) != 1:
            print(f'Signature {i + 1}/{len(list_sig)}: several solutions for (m, b), ignored (TODO: gcd on values "m")')
            continue
        
        m, b = leak[0]
        print(f'Signature {i + 1}/{len(list_sig)}: padded nonce mod {m} = {b}')

        B1 = (2**curve.order.bit_length() - b + 1) // m
        B2 = (2**curve.order.bit_length() + curve.order - b) // m

        C = (B1 + B2)//2
        LL = curve.order//(B2 - B1)

        tmp = invmod(s*m, curve.order)
        u = r*tmp % curve.order
        v = (msg - s*b)*tmp % curve.order
        vv = C - v
        
        Ui.append(u)
        Vi.append(vv)
        Li.append(LL)

    return Ui, Vi, Li


# multiplicative splitting

def dfa_swap_analysis_multsplit(curve, Q, QQ, skip, llambda):
    '''Returns candidates (m, lsb) such that lsb = gamma mod 2^skip and k = m*gamma mod curve.order'''

    if Q == QQ:
        return False, 0, 0

    QQ = curve.neg(QQ)
    diff = curve.add_aff(Q, QQ)
    tmp = curve.ladder(2**(skip + llambda), curve.base)
    diff = curve.add_aff(diff, tmp)
    
    try:
        dl = bsgs(curve, diff, curve.base, bounds=(0,2**(skip + llambda + 1)))
        dl = dl - 2**(skip + llambda)
        L = []
        for lsb in range(2**skip):
            t = 2*lsb - 2**skip
            if t == 0: continue
            if dl % t == 0:
                m = dl // t
                if m > 0 and m.bit_length() == llambda:
                    L.append((m, lsb))
                    
        if len(L) == 1:
            found = True
            m, lsb = L[0]
        else:
            found = False
            m, lsb = 0, 0
        
    except Exception as e:
        m, lsb = 0, 0
        found = False

    return found, m, lsb


def dfa_leak_from_sig_multsplit(curve, pubkey, msg, sig, skip, llambda):
    '''Returns validity of signature and list of potential leak candidates on the nonce'''

    valid, Q, QQ_list = points_from_sig(curve, pubkey, msg, sig)
    leak = []
    for QQ in QQ_list:
        found, m, lsb = dfa_swap_analysis_multsplit(curve, Q, QQ, skip, llambda)
        if found:
            leak.append((m, lsb))

    return valid, leak


def batch_analysis_ecdsa_multsplit(curve, pubkey, list_sig, skip, llambda):
    '''DFA analysis of list of signatures and prepare file for HNP (with mult. splitting of the nonce countermeeasure)'''

    Ui, Vi, Li = [], [], []
    for i in range(len(list_sig)):
        msg, r, s = list_sig[i]
        valid, leak = dfa_leak_from_sig_multsplit(curve, pubkey, msg, (r,s), skip, llambda)

        if valid:
            print(f'Signature {i + 1}/{len(list_sig)}: valid')
            continue
            
        if len(leak) != 1:
            print(f'Signature {i + 1}/{len(list_sig)}: no unique solution')
            continue

        m, lsb = leak[0]        
        print(f'Signature {i + 1}/{len(list_sig)}: random is {m} and gamma mod 2**{skip} = {lsb}')

        B1 = 0
        B2 = curve.order >> skip
        
        C = (B1 + B2)//2
        LL = curve.order//(B2 - B1)

        tmp = invmod(m*s*2**skip, curve.order)
        u = r*tmp % curve.order
        v = (msg - s*m*lsb)*tmp % curve.order
        vv = C - v

        Ui.append(u)
        Vi.append(vv)
        Li.append(LL)

    return Ui, Vi, Li


def batch_analysis_fixed_multsplit(curve, pubkey, list_points, skip, llambda):
    '''DFA analysis with fixed scalar and mult. splitting countermeasure, and prepare file for HNP'''

    Ui, Vi, Li = [], [], []
    for i in range(len(list_points)):
        QQ = list_points[i]
        found, m, lsb = dfa_swap_analysis_multsplit(curve, pubkey, QQ, skip, llambda)

        if not found:
            print(f'Point {i + 1}/{len(list_points)}: point correct or no unique solution')
            continue

        print(f'Point {i + 1}/{len(list_points)}: random is {m} and gamma mod 2**{skip} = {lsb}')
        
        B1 = 0
        B2 = curve.order >> skip

        C = (B1 + B2) // 2
        LL = curve.order // (B2 - B1)

        u = invmod(m*2**skip, curve.order)
        v = (-lsb*invmod(2**skip, curve.order)) % curve.order
        vv = C - v

        Ui.append(u)
        Vi.append(v)
        Li.append(LL)

    return Ui, Vi, Li
