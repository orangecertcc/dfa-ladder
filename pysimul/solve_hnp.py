#!/usr/bin/env python3

import sys
from fpylll import IntegerMatrix, BKZ
from pydfa.ec import *
from math import log2

def load_data(filename):

    f = open(filename, 'r')
    
    line = f.readline()
    sp = line.strip().split(',')
    curve_name = sp[0]
    curve = CurveJac(CURVES[curve_name])
    pubkey = curve.field(int(sp[1], 16)), curve.field(int(sp[2], 16))

    Ui, Vi, Li = [], [], []

    line = f.readline()
    while len(line) != 0:
        sp = line.strip().split(',')
        Ui.append(int(sp[0],16))
        Vi.append(int(sp[1],16))
        Li.append(int(sp[2]))
        line = f.readline()
        
    f.close()

    return curve, pubkey, Ui, Vi, Li


def generate_hnp_matrix(curve, Ui, Vi, Li):
    n = len(Ui)

    M = IntegerMatrix(n + 2, n + 2)
    for i in range(n):
        M[i, i] = 2*Li[i]*curve.order
        M[n, i] = 2*Li[i]*Ui[i]
        M[n + 1, i] = 2*Li[i]*Vi[i]
    M[n, n] = 1
    M[n + 1, n + 1] = curve.order

    return M
    

def solve_hnp(curve, pubkey, Ui, Vi, Li):

    # **approximately** determines a minimal number of signatures for HNP to work
    # it might avoids too large computation or on the contrary useless
    # computation when the number of elements is too low
    nbits = 0
    n = 0
    for L in Li:
        nbits += log2(L)
        n += 1
        if nbits >= curve.order.bit_length():
            break
    
    # we start with the first n elements
    while n <= len(Ui):
        print(f'HNP with {n} signatures...')
        M = generate_hnp_matrix(curve, Ui[:n], Vi[:n], Li[:n])
        Mreduced = BKZ.reduction(M, BKZ.Param(block_size=30))
        n += 1
        for i in range(Mreduced.nrows):
            row = Mreduced[i]
            key = abs(row[-2]) % curve.order
            if key == 0:
                continue
            Q = curve.ladder(key, curve.base)
            if Q[0] == pubkey[0]:
                if Q[1] == pubkey[1]:
                    return True, key
                else:
                    return True, curve.order - key
                
    return False, -1


def print_instructions():
    print('Command is "python3 solve_hnp.py filename')


if __name__ == "__main__":
    argc = len(sys.argv) - 1

    if argc != 1:
        print_instructions()
        sys.exit()

    try:
        filename = sys.argv[1]   
        curve, pubkey, Ui, Vi, Li = load_data(filename)

        print(f'Elliptic curve: {curve.name}')
        print(f'    Public key: ({pubkey[0].hex()},')
        print(f'                 {pubkey[1].hex()})')

        found, key = solve_hnp(curve, pubkey, Ui, Vi, Li)

        if found:
            print(f'Private key: {key}')
        else:
            print(f'Private key not found')

    except Exception as e:
        print(e)
        print_instructions()
    
