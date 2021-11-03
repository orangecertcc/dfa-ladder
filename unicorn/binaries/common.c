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

#include "common.h"

/* One converted into the Montgomery domain */
const BN_ULONG ONE[P256_LIMBS] = {
    TOBN(0x00000000, 0x00000001), TOBN(0xffffffff, 0x00000000),
    TOBN(0xffffffff, 0xffffffff), TOBN(0x00000000, 0xfffffffe)
};

/* Coordinates of G, for which we have precomputed tables */
const BN_ULONG def_xG[P256_LIMBS] = {
    TOBN(0x79e730d4, 0x18a9143c), TOBN(0x75ba95fc, 0x5fedb601),
    TOBN(0x79fb732b, 0x77622510), TOBN(0x18905f76, 0xa53755c6)
};

const BN_ULONG def_yG[P256_LIMBS] = {
    TOBN(0xddf25357, 0xce95560a), TOBN(0x8b4ab8e4, 0xba19e45c),
    TOBN(0xd2e88688, 0xdd21f325), TOBN(0x8571ff18, 0x25885d85)
};

/* r = in^-1 mod p */
void ecp_nistz256_mod_inverse(BN_ULONG r[P256_LIMBS],
                                     const BN_ULONG in[P256_LIMBS])
{
    /*
     * The poly is ffffffff 00000001 00000000 00000000 00000000 ffffffff
     * ffffffff ffffffff We use FLT and used poly-2 as exponent
     */
    BN_ULONG p2[P256_LIMBS];
    BN_ULONG p4[P256_LIMBS];
    BN_ULONG p8[P256_LIMBS];
    BN_ULONG p16[P256_LIMBS];
    BN_ULONG p32[P256_LIMBS];
    BN_ULONG res[P256_LIMBS];
    int i;

    ecp_nistz256_sqr_mont(res, in);
    ecp_nistz256_mul_mont(p2, res, in);         /* 3*p */

    ecp_nistz256_sqr_mont(res, p2);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(p4, res, p2);         /* f*p */

    ecp_nistz256_sqr_mont(res, p4);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(p8, res, p4);         /* ff*p */

    ecp_nistz256_sqr_mont(res, p8);
    for (i = 0; i < 7; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(p16, res, p8);        /* ffff*p */

    ecp_nistz256_sqr_mont(res, p16);
    for (i = 0; i < 15; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(p32, res, p16);       /* ffffffff*p */

    ecp_nistz256_sqr_mont(res, p32);
    for (i = 0; i < 31; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, in);

    for (i = 0; i < 32 * 4; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, p32);

    for (i = 0; i < 32; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, p32);

    for (i = 0; i < 16; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, p16);

    for (i = 0; i < 8; i++)
        ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, p8);

    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, p4);

    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, p2);

    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_sqr_mont(res, res);
    ecp_nistz256_mul_mont(res, res, in);

    memcpy(r, res, sizeof(res));
}

/* /\* */
/*  * Montgomery mul modulo Order(P): res = a*b*2^-256 mod Order(P) */
/*  *\/ */
/* void ecp_nistz256_ord_mul_mont(BN_ULONG res[P256_LIMBS], */
/*                                const BN_ULONG a[P256_LIMBS], */
/*                                const BN_ULONG b[P256_LIMBS]); */
/* void ecp_nistz256_ord_sqr_mont(BN_ULONG res[P256_LIMBS], */
/*                                const BN_ULONG a[P256_LIMBS], */
/*                                BN_ULONG rep); */

const u8 order[33] = {81, 37, 99, 252, 194, 202, 185, 243,
                      132, 158, 23, 167, 173, 250, 230, 188,
                      255, 255, 255, 255, 255, 255, 255, 255,
                      0, 0, 0, 0, 255, 255, 255, 255, 0};

/*
 * r = a + b
 */
void bn_add(u8 r[33], const u8 a[33], const u8 b[33]) {
    u8 tmp, carry = 0, carry1, carry2;
    int i;
    for (i = 0; i < 33; i++) {
        tmp = a[i] + b[i];
        carry1 = tmp < a[i];
        r[i] = tmp + carry;
        carry2 = r[i] < tmp;
        carry = carry1 | carry2;
    }
}

/*
 * r gets a if condition = 1, else b
 */
void bn_conditional_selection(const u8 condition, u8 r[33], const u8 a[33], const u8 b[33]) {
    u8 mask1, mask2;
    int i;
    mask1 = condition - 1;
    mask2 = ~mask1;

    for (i = 0; i < 33; i++) {
        r[i] = (a[i] & mask2) | (b[i] & mask1);
    }
}

int bn_is_bit_set(const u8 a[33], const int index) {
    int i, j;
    i = index / 8;
    j = index % 8;
    return (int)((a[i] >> j) & (u8)1);
}

/*
 * swaps a and b if condition = 1
 */
void bn_conditional_swap(const int condition, BN_ULONG a[P256_LIMBS], BN_ULONG b[P256_LIMBS]) {
    BN_ULONG mask;
    BN_ULONG tmp;
    int i;

    mask = 0 - (BN_ULONG)condition;

    for (i = 0; i < P256_LIMBS; i++) {
        tmp = a[i] ^ b[i];
        tmp &= mask;
        a[i] ^= tmp;
        b[i] ^= tmp;
    }
} 

u8 nibbleFromChar(char c) {
  if(c >= '0' && c <= '9') return (u8)(c - '0');
  if(c >= 'a' && c <= 'f') return (u8)(c - 'a' + 10);
  if(c >= 'A' && c <= 'F') return (u8)(c - 'A' + 10);
  return 255;
}

/* buf_in length must be two times length of buf_out */
void hexToBytes(const char *buf_in, u8 *buf_out, int len) {
  int pos;

  for (pos = 0 ; pos < len ; pos++) {
    buf_out[len - pos - 1] = (u8)((nibbleFromChar(buf_in[2*pos]) << 4) | nibbleFromChar(buf_in[2*pos + 1]));
  }
} 
