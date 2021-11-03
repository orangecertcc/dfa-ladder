#!/usr/bin/env python3

import argparse
import sys
from rainbow.generics import rainbow_x64

sys.path.insert(0, '../pysimul/')
from pydfa.ec import *
from pydfa.dfa_analysis import dfa_swap_analysis


def memcpy(em):
    r = em['rdi']
    res = em['rsi']
    em[r + 8*i] = bytes(em[res + 8*i])
    return True


def get_trace(fname, scalar):
    '''Runs a full execution of the scalar multiplication and traces all instructions'''
    
    e = rainbow_x64(sca_mode=True)
    e.load(fname, typ='.elf')
    e.stubbed_functions['memcpy'] = memcpy
    e.trace = True
    
    # load scalar in stack and reserve space
    # for the result of scalar multiplication
    scalar_addr = 0xdead0000
    res_addr = 0xbeef0000
    e[scalar_addr] = scalar.to_bytes(33, 'little')
    e[res_addr] = b'\x00'*64

    # load arguments and launch the full execution
    e['rdi'] = res_addr
    e['rsi'] = scalar_addr
    ret = e.start(e.functions['ladder_jac'], 0)

    result = b''
    for i in range(8):
        result += bytes(e[res_addr + 8*i])
    x = result[:32]
    y = result[32:]

    return e.sca_address_trace, (int.from_bytes(x, 'little'), int.from_bytes(y, 'little'))


def fault_simulation(fname, scalar, position, width, skip_min, skip_max):
    '''
    Executes many scalar multiplications with a same scalar,
    but a skip instruction in different positions in the interval [position - width, position + width]
    '''

    print('')
    curve = CurveJac(SECP256R1)
    padded_scalar = scalar_padding(curve, scalar)
    Q = curve.ladder(scalar, curve.base)

    results = []
    for pos in range(position - width, position + width + 1):
        try:
            e = rainbow_x64()
            e.load(fname, typ='.elf')
            e.stubbed_functions['memcpy'] = memcpy
            e.trace = False
            
            # load scalar in stack and reserve space
            # for the result of scalar multiolication
            scalar_addr = 0xdead0000
            res_addr = 0xbeef0000

            e[scalar_addr] = scalar.to_bytes(33, 'little')
            e[res_addr] = b'\x00'*64
            e['rdi'] = res_addr
            e['rsi'] = scalar_addr
            ret = e.start(e.functions['ladder_jac'], 0, count=pos)
            
            # get next instruction
            rip = e['rip']
            d = ''
            d = e.disassemble_single(rip, 8)
            print(f'Instruction skipped: {d}')
        
            # skip and resume
            ret = e.start(rip + d[1], 0)
            
            result = b''
            for i in range(8):
                result += bytes(e[res_addr + 8*i])
            xb = result[:32]
            yb = result[32:]

            print(f'  Output  : ({xb.hex()},{yb.hex()})')
            x = int.from_bytes(xb, 'little')
            y = int.from_bytes(yb, 'little')
            print(f'  On curve: {curve.is_on_curve((x,y))}')
            results.append((d, (x,y)))

            if d == '':
                print('')
                continue
            QQ_list = curve.lift_x(x % curve.order) # what we would get from a signature
            print(f'  # Q\'    : {len(QQ_list)}')
            ctr = 0
            for QQ in QQ_list:
                found, dl = dfa_swap_analysis(curve, Q, QQ, skip_max)
                if found:
                    # print(f'Instruction skipped: {d}')
                    # print(f'  on Curve: {on_curve}')
                    print(f'  Found   : {dl}  kpad mod 2^{skip_max}: {padded_scalar % 2**skip_max}')
                    print(f'  Reduced : {dl % 2**skip_min}  kpad mod 2^{skip_min}: {padded_scalar % 2**skip_min}')
                else:
                    ctr += 1
            if ctr == len(QQ_list):
                print('  Analysis found nothing')
            print('')
                    
        except Exception as ex:
            results.append((d, (0,0)))
        
    return results


if __name__ == "__main__":
    fname = 'binaries/ladderjac'
    
    try:
        parser = argparse.ArgumentParser(description='DFA simulation with Unicorn/Rainbow: Jacobian formulas')
        
        parser.add_argument('--scalar', action='store', dest='scalar', type=int,
                            help='Scalar', required=True)
        parser.add_argument('--inst', action='store', dest='position', type=int,
                            help='Position of instruction to skip', required=True)
        parser.add_argument('--width', action='store', dest='width', type=int, required=True)
        parser.add_argument('--skip', action='store', nargs=2, dest='skip', type=int,
                            help='loop iteration (min, max)', required=True)

        args = parser.parse_args()
        results = fault_simulation(fname, args.scalar, args.position, args.width, args.skip[0], args.skip[1])

    except Exception as ex:
        print(ex)

