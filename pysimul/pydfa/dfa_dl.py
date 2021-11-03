#!/usr/bin/env python3

from math import isqrt
from random import randint

## for Python versions < 3.8, remove the import of isqrt and use the code below
# def isqrt(n):
#     if n > 0:
#         x = 1 << (n.bit_length() + 1 >> 1)
#         while True:
#             y = (x + n // x) >> 1
#             if y >= x:
#                 return x
#             x = y
#     elif n == 0:
#         return 0
#     else:
#         raise ValueError("Square root not defined for negative numbers")


def bsgs(curve, b, a, bounds):
    '''
    Adapted from SageMath in the file src/sage/groups/generic.py
    Credits to the original author:
    - John Cremona (2008-03-15)
    '''
    lb, ub = bounds
    if lb < 0 or ub < lb:
        raise ValueError("bsgs() requires 0<=lb<=ub")
    
    ran = 1 + ub - lb   # the length of the interval

    tmp1 = curve.ladder(lb, a)
    tmp2 = curve.neg(b)
    c = curve.add_aff(tmp1, tmp2)

    if ran < 30:    # use simple search for small ranges
        d = c
        # for i,d in multiples(a,ran,c,indexed=True,operation=operation):
        for i0 in range(ran):
            i = lb + i0
            if curve.infty == d:        # identity == b^(-1)*a^i, so return i
                return i
            d = curve.add_aff(a, d)
        raise ValueError("No solution in bsgs()")

    m = isqrt(ran) + 1   # we need sqrt(ran) rounded up
    table = dict()       # will hold pairs (a^(lb+i),lb+i) for i in range(m)

    d = c
    for i0 in range(m):
        i = lb + i0
        if curve.infty == d:        # identity == b^(-1)*a^i, so return i
            return i
        table[d] = i
        d = curve.add_aff(d, a)

    c = curve.add_aff(c, curve.neg(d))     # this is now a**(-m)
    d = curve.infty
    for i in range(m):
        j = table.get(d)
        if j is not None:  # then d == b*a**(-i*m) == a**j
            return i * m + j
        d = curve.add_aff(c, d)

    raise ValueError(f"Log of {b} to the base {a} does not exist in {bounds}.")


## The code below could be used as a replacement for bsgs and needs less memory,
## but it takes longer time if the discrete log does not exist
# def discrete_log_lambda(curve, a, base, bounds, hash_function=hash):
#     '''
#     Adapted from SageMath in the file src/sage/groups/generic.py
#     Credits to the original author:
#         -- Yann Laigle-Chapuy (2009-01-25)
#     '''
  
#     lb, ub = bounds
#     if lb < 0 or ub < lb:
#         raise ValueError("discrete_log_lambda() requires 0<=lb<=ub")

#     width = ub - lb
#     N = isqrt(width) + 1

#     M = dict()
#     for s in range(10):  # to avoid infinite loops
#         # random walk function setup
#         k = 0
#         while 2**k < N:
#             r = randint(1, N - 1)
#             M[k] = (r, curve.ladder(r, base))
#             k += 1
#         # first random walk
#         H = curve.ladder(ub, base)
#         c = ub
#         for i in range(N):
#             r, e = M[hash_function(H) % k]
#             H = curve.add_aff(H, e)
#             c += r
#         mem = set([H])
#         # second random walk
#         H = a
#         d = 0
#         while c - d >= lb:
#             # print('mem:', mem)
#             if ub > c - d and H in mem:
#                 return c - d
#             r, e = M[hash_function(H) % k]
#             H = curve.add_aff(H, e)
#             d += r

#     raise ValueError("Pollard Lambda failed to find a log")

