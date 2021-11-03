/* 
 * Below are original references and copyright
 * All modifications are under the GPL v3 licence
 */

/*
 * Copyright 2014-2021 The OpenSSL Project Authors. All Rights Reserved.
 * Copyright (c) 2014, Intel Corporation. All Rights Reserved.
 * Copyright (c) 2015, CloudFlare, Inc.
 *
 * Licensed under the Apache License 2.0 (the "License").  You may not use
 * this file except in compliance with the License.  You can obtain a copy
 * in the file LICENSE in the source distribution or at
 * https://www.openssl.org/source/license.html
 *
 * Originally written by Shay Gueron (1, 2), and Vlad Krasnov (1, 3)
 * (1) Intel Corporation, Israel Development Center, Haifa, Israel
 * (2) University of Haifa, Israel
 * (3) CloudFlare, Inc.
 *
 * Reference:
 * S.Gueron and V.Krasnov, "Fast Prime Field Elliptic Curve Cryptography with
 *                          256 Bit Primes"
 */

#ifndef COMMON_H_
#define COMMON_H_

#include <string.h>
#include <stdio.h>

#define BN_ULONG unsigned long
#define BN_BYTES 8

#define BN_BITS2       (BN_BYTES * 8)
#define P256_LIMBS      (256/BN_BITS2)

#define TOBN(hi,lo)    ((BN_ULONG)hi<<32|lo)

typedef unsigned char u8;

/* Functions implemented in assembly */
/*
 * Most of below mentioned functions *preserve* the property of inputs
 * being fully reduced, i.e. being in [0, modulus) range. Simply put if
 * inputs are fully reduced, then output is too. Note that reverse is
 * not true, in sense that given partially reduced inputs output can be
 * either, not unlikely reduced. And "most" in first sentence refers to
 * the fact that given the calculations flow one can tolerate that
 * addition, 1st function below, produces partially reduced result *if*
 * multiplications by 2 and 3, which customarily use addition, fully
 * reduce it. This effectively gives two options: a) addition produces
 * fully reduced result [as long as inputs are, just like remaining
 * functions]; b) addition is allowed to produce partially reduced
 * result, but multiplications by 2 and 3 perform additional reduction
 * step. Choice between the two can be platform-specific, but it was a)
 * in all cases so far...
 */

/* Modular add: res = a+b mod P   */
void ecp_nistz256_add(BN_ULONG res[P256_LIMBS],
                      const BN_ULONG a[P256_LIMBS],
                      const BN_ULONG b[P256_LIMBS]);
/* Modular mul by 2: res = 2*a mod P */
void ecp_nistz256_mul_by_2(BN_ULONG res[P256_LIMBS],
                           const BN_ULONG a[P256_LIMBS]);
/* Modular mul by 3: res = 3*a mod P */
void ecp_nistz256_mul_by_3(BN_ULONG res[P256_LIMBS],
                           const BN_ULONG a[P256_LIMBS]);

/* Modular div by 2: res = a/2 mod P */
void ecp_nistz256_div_by_2(BN_ULONG res[P256_LIMBS],
                           const BN_ULONG a[P256_LIMBS]);
/* Modular sub: res = a-b mod P   */
void ecp_nistz256_sub(BN_ULONG res[P256_LIMBS],
                      const BN_ULONG a[P256_LIMBS],
                      const BN_ULONG b[P256_LIMBS]);
/* Modular neg: res = -a mod P    */
void ecp_nistz256_neg(BN_ULONG res[P256_LIMBS], const BN_ULONG a[P256_LIMBS]);
/* Montgomery mul: res = a*b*2^-256 mod P */
void ecp_nistz256_mul_mont(BN_ULONG res[P256_LIMBS],
                           const BN_ULONG a[P256_LIMBS],
                           const BN_ULONG b[P256_LIMBS]);
/* Montgomery sqr: res = a*a*2^-256 mod P */
void ecp_nistz256_sqr_mont(BN_ULONG res[P256_LIMBS],
                           const BN_ULONG a[P256_LIMBS]);
/* Convert a number from Montgomery domain, by multiplying with 1 */
void ecp_nistz256_from_mont(BN_ULONG res[P256_LIMBS],
                            const BN_ULONG in[P256_LIMBS]);
/* Convert a number to Montgomery domain, by multiplying with 2^512 mod P*/
void ecp_nistz256_to_mont(BN_ULONG res[P256_LIMBS],
                          const BN_ULONG in[P256_LIMBS]);


extern const BN_ULONG ONE[P256_LIMBS];
extern const BN_ULONG def_xG[P256_LIMBS];
extern const BN_ULONG def_yG[P256_LIMBS];

void ecp_nistz256_mod_inverse(BN_ULONG r[P256_LIMBS], const BN_ULONG in[P256_LIMBS]);

extern const u8 order[33];

/*
 * r = a + b
 */
void bn_add(u8 r[33], const u8 a[33], const u8 b[33]);
/*
 * r gets a if condition = 1, else b
 */
void bn_conditional_selection(const u8 condition, u8 r[33], const u8 a[33], const u8 b[33]);
int bn_is_bit_set(const u8 a[33], const int index);
/*
 * swaps a and b if condition = 1
 */
void bn_conditional_swap(const int condition, BN_ULONG a[P256_LIMBS], BN_ULONG b[P256_LIMBS]);


u8 nibbleFromChar(char c);

/* buf_in length must be two times length of buf_out */
void hexToBytes(const char *buf_in, u8 *buf_out, int len);


#endif /* COMMON_H_ */
