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
} P256_POINT;

/**
 * (r0, r1) -> (r0 + r1, r0 - r1)
 * inputs and outputs share the Z-coordinate (unused)
 */
void XYcoZ_addC(P256_POINT *r0, P256_POINT *r1) {
  BN_ULONG *t1 = r0->X;
  BN_ULONG *t2 = r0->Y;
  BN_ULONG *t3 = r1->X;
  BN_ULONG *t4 = r1->Y;
  BN_ULONG t5[P256_LIMBS];
  BN_ULONG t6[P256_LIMBS];
  BN_ULONG t7[P256_LIMBS];

  ecp_nistz256_sub(t5, t3, t1); 
  ecp_nistz256_sqr_mont(t5, t5);
  ecp_nistz256_mul_mont(t6, t1, t5);
  ecp_nistz256_mul_mont(t1, t3, t5);
  ecp_nistz256_add(t5, t4, t2);
  ecp_nistz256_sub(t4, t4, t2);
  ecp_nistz256_sub(t3, t1, t6);
  ecp_nistz256_mul_mont(t7, t2, t3);
  ecp_nistz256_add(t3, t1, t6);

  ecp_nistz256_sqr_mont(t1, t4);
  ecp_nistz256_sub(t1, t1, t3);
  ecp_nistz256_sub(t2, t6, t1);
  ecp_nistz256_mul_mont(t2, t4, t2);

  ecp_nistz256_sub(t2, t2, t7);
  ecp_nistz256_sqr_mont(t4, t5);
  ecp_nistz256_sub(t3, t4, t3);
  ecp_nistz256_sub(t4, t3, t6);
  ecp_nistz256_mul_mont(t4, t4, t5);
  ecp_nistz256_sub(t4, t4, t7);  
}

/**
 * (r0, r1) -> (r0 + r1, r0)
 * inputs and outputs share the Z-coordinate (unused)
 */
void XYcoZ_add(P256_POINT *r0, P256_POINT *r1) {
  BN_ULONG *t1 = r0->X;
  BN_ULONG *t2 = r0->Y;
  BN_ULONG *t3 = r1->X;
  BN_ULONG *t4 = r1->Y;
  BN_ULONG t5[P256_LIMBS];
  BN_ULONG t6[P256_LIMBS];
  
  ecp_nistz256_sub(t5, t3, t1);      /* X1 - X0 */
  ecp_nistz256_sqr_mont(t5, t5);     /* (X1 - X0)^2    = A */
  ecp_nistz256_mul_mont(t6, t3, t5); /* X1*(X1 - X0)^2 = B */
  ecp_nistz256_mul_mont(t3, t1, t5); /* X0*(X1 - X0)^2 = C */
  ecp_nistz256_sub(t5, t4, t2);      /* Y1 - Y0 */
  ecp_nistz256_sqr_mont(t1, t5);     /* (Y1 - Y0)^2 */
  ecp_nistz256_sub(t1, t1, t3);      /* (Y1 - Y0)^2 - C */
  
  ecp_nistz256_sub(t1, t1, t6);      /* (Y1 - Y0)^2 - C - B = X3*/
  ecp_nistz256_sub(t6, t6, t3);      /* B - C = (X1 - X0)^3 */
  ecp_nistz256_mul_mont(t4, t2, t6); /* Y0*(X1 - X0)^3 */
  ecp_nistz256_sub(t2, t3, t1);      /* C - X3 */
  ecp_nistz256_mul_mont(t2, t5, t2); /* (Y1 - Y0)*(C - X3) */
  ecp_nistz256_sub(t2, t2, t4);      /* (Y1 - Y0)*(C - X3) - Y0*(X1 - X0)^3 */
}

/**
 * (r0, r1) -> (r1 - r0, r0)
 * inputs and outputs share the Z-coordinate (unused)
 * r1 - r0 is supposed to be the loop invariant (equals to the base point)
 */
void XYcoZ_getinvariant(P256_POINT *r0, P256_POINT *r1) {
  BN_ULONG *t1 = r0->X;
  BN_ULONG *t2 = r0->Y;
  BN_ULONG *t3 = r1->X;
  BN_ULONG *t4 = r1->Y;
  BN_ULONG t5[P256_LIMBS];
  BN_ULONG t6[P256_LIMBS];
  
  ecp_nistz256_sub(t5, t3, t1);      /* X1 - X0 */
  ecp_nistz256_sqr_mont(t5, t5);     /* (X1 - X0)^2    = A */
  ecp_nistz256_mul_mont(t6, t3, t5); /* X1*(X1 - X0)^2 = B */
  ecp_nistz256_mul_mont(t3, t1, t5); /* X0*(X1 - X0)^2 = C */
  
  ecp_nistz256_add(t5, t4, t2);      /* Y1 + Y0 */
  ecp_nistz256_sqr_mont(t1, t5);     /* (Y1 + Y0)^2 */
  ecp_nistz256_sub(t1, t1, t3);      /* (Y1 + Y0)^2 - C */
  
  ecp_nistz256_sub(t1, t1, t6);      /* (Y1 - Y0)^2 - C - B = X3*/
  ecp_nistz256_sub(t6, t6, t3);      /* B - C = (X1 - X0)^3 */
  ecp_nistz256_mul_mont(t4, t2, t6); /* Y0*(X1 - X0)^3 */
  ecp_nistz256_sub(t2, t3, t1);      /* C - X3 */
  ecp_nistz256_mul_mont(t2, t5, t2); /* (Y1 + Y0)*(C - X3) */
  ecp_nistz256_add(t2, t2, t4);      /* (Y1 + Y0)*(C - X3) + Y0*(X1 - X0)^3 */
}

/* (X:Y:) |-> (z^2*X:z^3*Y:) */ 
void apply_z(P256_POINT *p, const BN_ULONG *z) {
  BN_ULONG t1[P256_LIMBS];

  ecp_nistz256_sqr_mont(t1, z);
  ecp_nistz256_mul_mont(p->X, p->X, t1);
  ecp_nistz256_mul_mont(t1, t1, z);
  ecp_nistz256_mul_mont(p->Y, p->Y, t1);
}

void XYcoZ_initdbljac(P256_POINT *r0, P256_POINT *r1, const P256_POINT *p, const BN_ULONG *initial_Z) {
  int i;
  BN_ULONG *t1 = r0->X;
  BN_ULONG *t2 = r0->Y;
  BN_ULONG *t3 = r1->X;
  BN_ULONG *t4 = r1->Y;
  BN_ULONG t5[P256_LIMBS];
  BN_ULONG t6[P256_LIMBS];
  BN_ULONG t7[P256_LIMBS];
  BN_ULONG z[P256_LIMBS];
  P256_POINT pp;

  for (i = 0; i < P256_LIMBS; i++) {
    pp.X[i] = p->X[i];
    pp.Y[i] = p->Y[i];
  }

  /* if initial_Z is provided the point coordinates are randomized */
  if (initial_Z) {
    ecp_nistz256_to_mont(z, initial_Z);
    apply_z(&pp, z);
  }
  else {
    for (i = 0; i < P256_LIMBS; i++) {
      z[i] = ONE[i];
    }
  }

  ecp_nistz256_sqr_mont(t7, pp.X);
  ecp_nistz256_add(t2, t7, t7);
  ecp_nistz256_add(t7, t7, t2);
  ecp_nistz256_sqr_mont(t1, z);
  ecp_nistz256_sqr_mont(t1, t1);

  ecp_nistz256_add(t5, t1, t1);
  ecp_nistz256_add(t5, t5, t1);
  ecp_nistz256_sub(t7, t7, t5);

  ecp_nistz256_sqr_mont(t2, pp.Y);
  ecp_nistz256_add(t2, t2, t2);
  ecp_nistz256_add(t5, t2, t2);
  ecp_nistz256_mul_mont(t1, t5, pp.X);
  ecp_nistz256_sqr_mont(t6, t7);

  ecp_nistz256_sub(t6, t6, t1);
  ecp_nistz256_sub(t3, t6, t1);
  ecp_nistz256_sub(t6, t1, t3);

  ecp_nistz256_mul_mont(t6, t6, t7);
  ecp_nistz256_sqr_mont(t2, t2);
  ecp_nistz256_add(t2, t2, t2);
  ecp_nistz256_sub(t4, t6, t2);
}

/*
 * swaps points a and b if condition = 1
 */
void point_conditional_swap(const int condition, P256_POINT *a, P256_POINT *b) {
    bn_conditional_swap(condition, a->X, b->X);
    bn_conditional_swap(condition, a->Y, b->Y);
}


void print_point(P256_POINT *r, const char *s) {
  int i;
  BN_ULONG x[P256_LIMBS];

  ecp_nistz256_from_mont(x, r->X);
  for (i = 0; i < P256_LIMBS; i++) {
    fprintf(stderr, "%016lx", x[P256_LIMBS - i - 1]);
  }
  fprintf(stderr, ",");
  ecp_nistz256_from_mont(x, r->Y);
  for (i = 0; i < P256_LIMBS; i++) {
    fprintf(stderr, "%016lx", x[P256_LIMBS - i - 1]);
  }
  fprintf(stderr, "    %s\n", s);
}

/* Expects scalars in range [2, q-3] */
/* (Co-Z formulas should not work for scalars 0, 1, q-1 and q-2) */
void ladder_XYcoZ(P256_POINT *r, const u8 scalar[33], const BN_ULONG *initial_Z) {
    int i, kbit, pbit;
    P256_POINT r0;
    P256_POINT r1;
    P256_POINT p;
    BN_ULONG z[P256_LIMBS];
    u8 kpad1[33] = {0};
    u8 kpad2[33] = {0};

    /* scalar padding */
    /*  kpad1 = scalar + order */
    /*  kpad2 = scalar + 2*order */
    /* if kpad1 is not a 257-bit integer, we select kpad2 instead */
    bn_add(kpad1, scalar, order);
    bn_add(kpad2, kpad1, order);
    bn_conditional_selection(kpad1[32], kpad1, kpad1, kpad2);

    for (i = 0; i < P256_LIMBS; i++) {
      p.X[i] = def_xG[i];
      p.Y[i] = def_yG[i];
    }
        
    XYcoZ_initdbljac(&r0, &r1, &p, initial_Z);
    
    pbit = 0;
    for (i = 255; i >= 0; i--) {
        kbit = bn_is_bit_set(kpad1, i);
        pbit ^= kbit;
        point_conditional_swap(pbit, &r0, &r1);
        pbit = kbit;

        XYcoZ_addC(&r0, &r1); /* (r0, r1) <- (r0 + r1, r0 - r1) */ 
        XYcoZ_add(&r0, &r1);  /* (r0, r1) <- (r0 + r1, r1') */
    }
    point_conditional_swap(kbit, &r0, &r1);
    /* (r0, r1) = ([k]P, [k+1]P) */
    XYcoZ_getinvariant(&r0, &r1);
    /* Now we have (r0, r1) = (invariant, [k]P) */

    /* recovery of the missing Z-coordinate */
    ecp_nistz256_mul_mont(z, r0.Y, p.X);
    ecp_nistz256_mod_inverse(z, z);
    ecp_nistz256_mul_mont(z, z, p.Y);
    ecp_nistz256_mul_mont(z, z, r0.X);

    apply_z(&r0, z);
    apply_z(&r1, z);

    /* output XOR calculated invariant XOR correct invariant */
    for (i = 0; i < P256_LIMBS; i++) {
      r1.X[i] ^= (r0.X[i] ^ p.X[i]);
      r1.Y[i] ^= (r0.Y[i] ^ p.Y[i]);
    }

    /* back from Montgomery representation */
    ecp_nistz256_from_mont(r->X, r1.X);
    ecp_nistz256_from_mont(r->Y, r1.Y);
}

int main(int argc, char *argv[]) {
    u8 scalar[33] = {0};
    int i, ret = 0;
    P256_POINT r;
    BN_ULONG *initial_Z = NULL;
    FILE *fp = NULL;

    if (argc != 2) {
      fprintf(stderr, "Argument missing\n");
      ret = 1;
      goto err;
    }

    hexToBytes(argv[1], scalar, 32);

    ladder_XYcoZ(&r, scalar, initial_Z);

    /* write result in a file */
    /* format: "scalar,x,y"   */
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
