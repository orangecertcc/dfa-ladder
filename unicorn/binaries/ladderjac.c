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

typedef struct {
    BN_ULONG X[P256_LIMBS];
    BN_ULONG Y[P256_LIMBS];
    BN_ULONG Z[P256_LIMBS];
} P256_POINT;

/* used both for affine and XY(only)coZ */
typedef struct {
    BN_ULONG X[P256_LIMBS];
    BN_ULONG Y[P256_LIMBS];
} P256_POINT_AFFINE;

void ecp_nistz256_point_double(P256_POINT *r, const P256_POINT *a);
void ecp_nistz256_point_add(P256_POINT *r,
                            const P256_POINT *a, const P256_POINT *b);

/*
 * swaps points a and b if condition = 1
 */
void point_conditional_swap(const int condition, P256_POINT *a, P256_POINT *b) {
    bn_conditional_swap(condition, a->X, b->X);
    bn_conditional_swap(condition, a->Y, b->Y);
    bn_conditional_swap(condition, a->Z, b->Z);
}

void ladder_jac(P256_POINT_AFFINE *r, const u8 scalar[33]) {
    int i, kbit, pbit;
    P256_POINT r0;
    P256_POINT r1;
    BN_ULONG Z_inv2[P256_LIMBS], Z_inv3[P256_LIMBS], x_aff[P256_LIMBS], y_aff[P256_LIMBS];
    u8 kpad1[33] = {0};
    u8 kpad2[33] = {0};

    /* scalar padding */
    /*  kpad1 = scalar + order */
    /*  kpad2 = scalar + 2*order */
    /* if kpad1 is not a 257-bit integer, we select kpad2 instead */
    bn_add(kpad1, scalar, order);
    bn_add(kpad2, kpad1, order);
    bn_conditional_selection(kpad1[32], kpad1, kpad1, kpad2);

    /* ladder initialization: */
    /*   R0 = P    */
    /*   R1 = [2]P */
    for (i = 0; i < P256_LIMBS; i++) {
        r0.X[i] = def_xG[i];
        r0.Y[i] = def_yG[i];
        r0.Z[i] = ONE[i];
    }

    /* init: (r0, r1) = (P, [2]P); */
    ecp_nistz256_point_double(&r1, &r0);

    pbit = 0;
    for (i = 255; i >= 0; i--) {
        kbit = bn_is_bit_set(kpad1, i);
        pbit ^= kbit;
        point_conditional_swap(pbit, &r0, &r1);
        pbit = kbit;

        ecp_nistz256_point_add(&r1, &r0, &r1);
        ecp_nistz256_point_double(&r0, &r0);
    }

    point_conditional_swap(pbit, &r0, &r1);

    /* convert to affine */
    ecp_nistz256_mod_inverse(Z_inv3, r0.Z);        /* Z^-1 */
    ecp_nistz256_sqr_mont(Z_inv2, Z_inv3);         /* Z^-2 */
    ecp_nistz256_mul_mont(Z_inv3, Z_inv2, Z_inv3); /* Z^-3 */

    ecp_nistz256_mul_mont(x_aff, Z_inv2, r0.X);
    ecp_nistz256_mul_mont(y_aff, Z_inv3, r0.Y);

    /* back from Montgomery representation */
    ecp_nistz256_from_mont(r->X, x_aff);
    ecp_nistz256_from_mont(r->Y, y_aff);
}

int main(int argc, char *argv[]) {
    u8 scalar[33] = {0};
    int i, ret = 0;
    P256_POINT_AFFINE r;
    FILE *fp = NULL;

    if (argc != 2) {
      fprintf(stderr, "Argument missing\n");
      ret = 1;
      goto err;
    }
    
    hexToBytes(argv[1], scalar, 32);

    ladder_jac(&r, scalar);

    /* write result in a file */
    /* format: "scalar,X,Y"   */
    fp = fopen("output.txt", "a");
    if (fp == NULL) {
        ret = 1;
        goto err;
    }
    for (i = 0; i < 32; i++) {
        fprintf(fp, "%02x", scalar[31 - i]);
    }
    fprintf(fp, ",");
    for (i = 0; i < P256_LIMBS; i++) {
        fprintf(fp, "%016lx", r.X[P256_LIMBS - i - 1]);
    }
    fprintf(fp, ",");
    for (i = 0; i < P256_LIMBS; i++) {
        fprintf(fp, "%016lx", r.Y[P256_LIMBS - i - 1]);
    }
    fprintf(fp, "\n");

err:
    fclose(fp);
    return ret;
}
