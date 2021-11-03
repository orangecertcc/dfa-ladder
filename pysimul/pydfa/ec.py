#!/usr/bin/env python3

from random import randint

# FLT inversion when m is prime
invmod = lambda a, m : pow(a, m - 2, m)

class FieldElement:
    def __init__(self, a, field):
        self.field = field
        self.a = a % self.field.p

    def __add__(self, other):
        return FieldElement(self.a + other.a, self.field)

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        return FieldElement(self.a - other.a, self.field)

    def __rsub__(self, other):
        return self - other

    def __neg__(self):
        return FieldElement(-self.a, self.field)

    def __mul__(self, other):
        if isinstance(other, int):
            return FieldElement(self.a*other, self.field)
        return FieldElement(self.a*other.a, self.field)

    def __rmul__(self, other):
        return self*other

    def invert(self):
        if self.a == 0:
            raise ZeroDivisionError
        return FieldElement(invmod(self.a, self.field.p), self.field)

    def __truediv__(self, other):
        return self*invert(other)

    def __pow__(self, exp : int):
        if exp < 0:
            return self.invert()**(-exp)
        return FieldElement(pow(self.a, exp, self.field.p), self.field)

    def __eq__(self, other):
        if isinstance(other, int):
            return self == FieldElement(other, self.field)
        return self.a == other.a and self.field.p == other.field.p

    def __neq__(self, other):
        return not self == other

    def __str__(self):
        return str(self.a)

    def __repr__(self):
        return str(self.a)

    def hex(self):
        return hex(self.a)

    def to_int(self):
        return self.a

    def legendre_symbol(self):
        return self**((self.field.p - 1)//2)

    def sqrt(self):
        '''https://eli.thegreenplace.net/2009/03/07/computing-modular-square-roots-in-python'''

        if self.legendre_symbol() != 1:
            return 0
        elif self == 0:
            return self
        elif self.field.p % 4 == 3:
            return self**((self.field.p + 1)//4)

        s = self.field.p - 1
        e = 0
        while s % 2 == 0:
            s //= 2
            e += 1

        n = self.field(2)
        while n.legendre_symbol() != -1:
            n = n + 1

        x = a**((s + 1)//2)
        b = a**s
        g = n**s
        r = e

        while True:
            t = b
            m = 0
            for m in xrange(r):
                if t == 1:
                    break
                t = t**2

            if m == 0:
                return x

            gs = g**(2**(r - m - 1))
            g = gs*gs
            x = x*gs
            b = b*g
            r = m

    def __hash__(self):
        return hash(self.a)


class PrimeField:
    def __init__(self, prime):
        self.p = prime

    def __call__(self, a):
        return FieldElement(a, self)


def conditional_swap(bit, R0, R1):
    if bit == 1:
        R0, R1 = R1, R0
    return R0, R1


class Curve:
    def __init__(self, params):
        self.name = params['name']
        self.field = PrimeField(params['p'])
        self.A = self.field(params['A'])
        self.B = self.field(params['B'])
        self.order = params['order']
        self.base = self.field(params['x0']), self.field(params['y0'])

    def is_on_curve(self, P):
        x = self.field(P[0])
        y = self.field(P[1])
        
        t0 = x**2
        t0 = t0 + self.A
        t0 = t0*x
        t0 = t0 + self.B
        t1 = y**2
        return t0 == t1

    def lift_x(self, r):
        '''
        find (x,y) on curve such that x mod curve.order = r
        and 0 <= r < curve.order
        '''
        assert 0 <= r and r < self.order
            
        Lx = []
        # find potential x
        while r < self.field.p:
            Lx.append(self.field(r))
            r += self.order

        lifted_points = []
        for x in Lx:
            ysqr = x**2
            ysqr = ysqr + self.A
            ysqr = ysqr*x
            ysqr = ysqr + self.B
            y = ysqr.sqrt()
            # case ysqr is not a square
            if y == 0 and ysqr != 0:
                continue
            # We add the points
            lifted_points += [(x, y), (x, -y)]
            
        return lifted_points

    def neg(self, P):
        '''point negation (P in affine form)'''
        if P == self.infty:
            return self.infty
        return P[0], -P[1]
          
    def dbl_aff(self, P):
        '''https://hyperelliptic.org/EFD/g1p/auto-shortw-projective.html#doubling-mdbl-2007-bl'''
        if P == self.infty:
            return P

        X1, Y1 = P
        
        XX = X1**2
        t0 = 3*XX
        w = self.A + t0
        Y1Y1 = Y1**2
        R = 2*Y1Y1
        t1 = Y1*R
        sss = 4*t1
        RR = R**2
        t2 = X1 + R
        t3 = t2**2
        t4 = t3 - XX
        B = t4 - RR
        t5 = w**2
        t6 = 2*B
        h = t5 - t6
        t7 = h*Y1
        X3 = 2*t7
        t8 = B - h
        t9 = 2*RR
        t10 = w*t8
        Y3 = t10 - t9
        Z3 = sss

        t = Z3**-1
        return X3*t, Y3*t
        
    def add_aff(self, P, Q):
        '''https://hyperelliptic.org/EFD/g1p/auto-shortw-projective.html#addition-mmadd-1998-cmo'''
        if P == self.infty:
            return Q
        if Q == self.infty:
            return P
                
        X1, Y1 = P
        X2, Y2 = Q

        if X1 == X2:
            if Y1 == Y2:
                return self.dbl_aff(P)
            return self.infty
        
        u = Y2 - Y1
        uu = u**2
        v = X2 - X1
        vv = v**2
        vvv = v*vv
        R = vv*X1
        t0 = 2*R
        t1 = uu - vvv
        A = t1 - t0
        X3 = v*A
        t2 = R - A
        t3 = vvv*Y1
        t4 = u*t2
        Y3 = t4 - t3
        Z3 = vvv

        t = Z3**-1        
        return X3*t, Y3*t


class CurveJac(Curve):

    def __init__(self, params):
        Curve.__init__(self, params)
        self.type = 'Jac'
        self.infty = self.field(1), self.field(1), self.field(0)
     
    def to_affine(self, P):
        X, Y, Z = P
        if Z == 0:
            return self.infty
        tcub = Z**-1
        tsqr = tcub**2
        tcub = tsqr*tcub
        return X*tsqr, Y*tcub
 
    def add_jac(self, P1, P2):
        '''https://hyperelliptic.org/EFD/g1p/auto-shortw-jacobian.html#addition-add-2007-bl'''

        X1, Y1, Z1 = P1
        X2, Y2, Z2 = P2

        if Z1 == 0:
            return P2
        if Z2 == 0:
            return P1

        Z1Z1 = Z1**2
        Z2Z2 = Z2**2
        U1 = X1*Z2Z2
        U2 = X2*Z1Z1
        t0 = Z2*Z2Z2
        S1 = Y1*t0
        t1 = Z1*Z1Z1
        S2 = Y2*t1
        H = U2 - U1
        t2 = 2*H
        I = t2**2
        J = H*I
        t3 = S2 - S1
        if H == 0:
            if t3 == 0:
                return self.dbl_jac(P1)
            else:
                return self.infty
        r = 2*t3
        V = U1*I
        t4 = r**2
        t5 = 2*V
        t6 = t4 - J
        X3 = t6 - t5
        t7 = V - X3
        t8 = S1*J
        t9 = 2*t8
        t10 = r*t7
        Y3 = t10 - t9
        t11 = Z1 + Z2
        t12 = t11**2
        t13 = t12 - Z1Z1
        t14 = t13 - Z2Z2
        Z3 = t14*H

        return X3, Y3, Z3
      
    def dbl_jac(self, P1):
        '''https://hyperelliptic.org/EFD/g1p/auto-shortw-jacobian.html#doubling-dbl-2007-bl'''

        X1, Y1, Z1 = P1
        if Z1 == 0:
            return P1

        XX = X1**2
        YY = Y1**2
        YYYY = YY**2
        ZZ = Z1**2
        t0 = X1 + YY
        t1 = t0**2
        t2 = t1 - XX
        t3 = t2 - YYYY
        S = 2*t3
        t4 = ZZ**2
        t5 = self.A*t4
        t6 = 3*XX
        M = t6 + t5
        t7 = M**2
        t8 = 2*S
        T = t7 - t8
        X3 = T
        t9 = S - T
        t10 = 8*YYYY
        t11 = M*t9
        Y3 = t11 - t10
        t12 = Y1 + Z1
        t13 = t12**2
        t14 = t13 - YY
        Z3 = t14 - ZZ
        return X3, Y3, Z3

    def ladder(self, k, P, skip=-1):
        if k == 0:
            return self.infty
        if k == 1:
            return P
        
        n = k.bit_length()
        R0 = P[0], P[1], self.field(1)
        R1 = self.dbl_jac(R0)

        condition = 0
        for i in range(n - 2, -1, -1):
            ki = (k >> i) & 1
            condition ^= ki
            R0, R1 = conditional_swap(condition, R0, R1)
            R1 = self.add_jac(R0, R1)
            R0 = self.dbl_jac(R0)
            if i != skip: condition = ki # fault on step "skip"

        R0, R1 = conditional_swap(k & 1, R0, R1)

        return self.to_affine(R0)


class CurveXZ(Curve):

    def __init__(self, params):
        Curve.__init__(self, params)
        self.typ = 'XZ'
        self.B2 = self.B*2
        self.B4 = self.B2*2
        self.infty = self.field(0), self.field(1), self.field(0)

    def to_affine(self, P):
        if P[2] == 0:
            return self.infty
        t = P[2]**-1
        return P[0]*t, P[1]*t
    
    def y_recovery(self, P, R0, R1):

        x0, y0 = P
        X1, Z1 = R0
        X2, Z2 = R1
        A = x0*Z1
        B = A - X1
        B = B**2
        C = x0*X1
        D = self.A*Z1
        A = A + X1
        E = C + D
        A = A*E
        C = Z1*Z2
        D = y0*C
        D = 2*D
        C = self.B2*C
        X = D*X1
        Z = D*Z1
        A = A*Z2
        B = B*X2
        A = A - B
        C = C*Z1
        Y = A + C

        return X, Y, Z

    def add_xz(self, P1, P2, x0):
        '''https://hyperelliptic.org/EFD/g1p/auto-shortw-xz.html#diffadd-mdadd-2002-it-4'''
        
        X1, Z1 = P1
        X2, Z2 = P2
        
        T1 = X1*X2
        T2 = Z1*Z2
        T3 = X1*Z2
        T4 = X2*Z1
        T5 = T3 + T4
        T6 = self.A*T2
        T7 = T1 + T6
        T8 = T5*T7
        T9 = 2*T8
        T10 = T2**2
        T11 = self.B*T10
        T12 = 4*T11
        T13 = T9 + T12
        T14 = T3 - T4
        Z3 = T14**2
        T17 = x0*Z3
        X3 = T13 - T17

        return X3, Z3

    def dbl_xz(self, P1):
        '''https://hyperelliptic.org/EFD/g1p/auto-shortw-xz.html#doubling-dbl-2002-bj-3'''
        
        X1, Z1 = P1
        
        XX = X1**2
        ZZ = Z1**2
        t0 = X1 + Z1
        t1 = t0**2
        t2 = t1 - XX
        t3 = t2 - ZZ
        A = 2*t3
        aZZ = self.A*ZZ
        t4 = XX - aZZ
        t5 = t4**2
        t6 = A*ZZ
        t7 = self.B2*t6
        X3 = t5 - t7
        t8 = XX + aZZ
        t9 = ZZ**2
        t10 = self.B4*t9
        t11 = A*t8
        Z3 = t11 + t10
    
        return X3, Z3

    def ladder(self, k, P, skip=-1):

        if k == 0:
            return self.infty
        if k == 1:
            return P
        
        n = k.bit_length()
        R0 = P[0], self.field(1)
        R1 = self.dbl_xz(R0)

        condition = 0
        for i in range(n - 2, -1, -1):
            ki = (k >> i) & 1
            condition ^= ki
            R0, R1 = conditional_swap(condition, R0, R1)
            R1 = self.add_xz(R0, R1, P[0])
            R0 = self.dbl_xz(R0)
            if i != skip: condition = ki # fault on step "skip"
        R0, R1 = conditional_swap(k & 1, R0, R1)
        R = self.y_recovery(P, R0, R1)
        
        return self.to_affine(R)

    
class CurveCoZ(Curve):

    def __init__(self, params):
        Curve.__init__(self, params)
        self.type = 'CoZ'
        self.infty = self.field(1), self.field(1), self.field(0)
        
    def Z_recovery(self, bit, P, R0, R1):
        x, y = P
        X0 = R0[0]
        X1, Y1 = R1
        t = X1 - X0
        t = t*Y1
        t = t*x
        t = t**-1
        u = X1*y
        u = (-1)**(1 - bit)*u
        t = u*t
        lambdaX = t**2
        lambdaY = t*lambdaX
        return lambdaX, lambdaY
    
    def XYCZadd(self, P1, P2):
        '''Output: (P1 + P2, P1)'''

        t1, t2 = P1
        t3, t4 = P2
        
        t5 = t3 - t1
        t5 = t5**2
        t6 = t3*t5
        t3 = t1*t5
        t5 = t4 - t2
        t1 = t5**2
        t1 = t1 - t3
    
        t1 = t1 - t6
        t6 = t6 - t3
        t4 = t2*t6
        t2 = t3 - t1
        t2 = t5*t2
        t2 = t2 - t4
        
        return (t1, t2), (t3, t4)

    def XYCZaddC(self, P1, P2):
        '''Output: (P1 + P2, P1 - P2)'''
        t1, t2 = P1
        t3, t4 = P2
        
        t5 = t3 - t1
        t5 = t5**2
        t6 = t1*t5
        t1 = t3*t5
        t5 = t4 + t2
        t4 = t4 - t2
        t3 = t1 - t6
        t7 = t2*t3
        t3 = t1 + t6
        
        t1 = t4**2
        t1 = t1 - t3
        t2 = t6 - t1
        t2 = t4*t2
        
        t2 = t2 - t7
        t4 = t5**2
        t3 = t4 - t3
        t4 = t3 - t6
        t4 = t4*t5
        t4 = t4 - t7
        
        return (t1, t2), (t3, t4)

    def XYCZdblJac(self, P):
        '''Output: (2*P, P)'''
        X, Y, Z = P
        
        t7 = X**2
        t4 = t7 + t7
        t7 = t7 + t4
        t3 = Z**2
        t3 = t3**2
        
        t5 = t3 + t3
        t5 = t5 + t3
        t7 = t7 - t5
        
        t4 = Y**2
        t4 = t4 + t4
        t5 = t4 + t4
        t3 = t5*X
        t6 = t7**2
        
        t6 = t6 - t3
        t1 = t6 - t3
        t6 = t3 - t1
        
        t6 = t6*t7
        t4 = t4**2
        t4 = t4 + t4
        t2 = t6 - t4
        
        return (t1, t2), (t3, t4)

    def ladder(self, k, P, skip=-1):

        if k == 0:
            return self.infty
        if k == 1:
            return P
        
        x, y = P
        R1, R0 = self.XYCZdblJac((x, y, self.field(1)))

        n = k.bit_length()
        condition = 0
        for i in range(n - 2, 0, -1):
            ki = (k >> i) & 1
            condition ^= ki
            R0, R1 = conditional_swap(condition, R0, R1)
            R0, R1 = self.XYCZaddC(R0, R1)
            R0, R1 = self.XYCZadd(R0, R1)
            if i != skip: condition = ki # fault on step "skip"

        # processing last bit and recovery of missing Z coordinate
        ki = k & 1
        condition ^= ki
        R0, R1 = conditional_swap(condition, R0, R1)
        R0, R1 = self.XYCZaddC(R0, R1)
        lambdaX, lambdaY = self.Z_recovery(ki, P, R0, R1)
        R0, R1 = self.XYCZadd(R0, R1)
        R0, R1 = conditional_swap(ki, R0, R1)
        X, Y = R0
        return X*lambdaX, Y*lambdaY


## scalar multiplications with different randomization methods

def scalar_padding(curve, k):
    kpad = k + curve.order
    if kpad.bit_length() != curve.order.bit_length() + 1:
        kpad += curve.order
    return kpad


def scalar_mult_padding(curve, k, base, skip=-1, llambda=20):
    '''padding on scalar: k + e*order with e in {1, 2}'''
    kpad = scalar_padding(curve, k)
    return curve.ladder(kpad, base, skip)


def scalar_mult_blinding(curve, k, base, skip=-1, llambda=20):
    '''blinded scalar: k + random*order'''
    m = randint(2**(llambda - 1), 2**llambda - 1)
    kblinded = k + m*curve.order
    return curve.ladder(kblinded, base, skip)


def scalar_mult_splitting_mult(curve, k, base, skip=-1, llambda=20):
    '''splitted scalar: k = random*gamma'''
    m = randint(2**(llambda - 1), 2**llambda - 1)
    minv = invmod(m, curve.order)
    gamma = k*minv % curve.order
    R = curve.ladder(m, base)
    Q = curve.ladder(gamma, R, skip) # fault on this scalar multiplication
    return Q


def scalar_mult_splitting_eucl(curve, k, base, skip=-1, llambda=-1):
    '''splitted scalar: k = a*random + b'''
    m = randint(2**(llambda - 1), 2**llambda - 1)
    kpad = scalar_padding(curve, k)
    a = kpad // m
    b = kpad % m

    R = curve.ladder(a, base)
    S = curve.ladder(m, R, skip) # fault on this scalar multiplication
    T = curve.ladder(b, base)
    return curve.add_aff(S, T)


## ECDSA

def ecdsa_sign(curve, privkey, msg, ecsm_func, skip=-1, llambda=20):
    while True:
        k = randint(1, curve.order - 1)
        x, y = ecsm_func(curve, k, curve.base, skip, llambda)
        r = x.to_int() % curve.order
        kinv = invmod(k, curve.order)
        s = kinv*(msg + privkey*r) % curve.order
        if r != 0 and s != 0:
            break
    return r, s


def ecdsa_verify(curve, pubkey, msg, sig):
    r, s = sig
    sinv = invmod(s, curve.order)
    u = msg*sinv % curve.order
    v = r*sinv % curve.order
    U = curve.ladder(u, curve.base)
    V = curve.ladder(v, pubkey)
    Q = curve.add_aff(U, V)
    return Q[0].to_int() % curve.order == r, Q


## gen keypair

def generate_keypair(curve):
    privkey = randint(1, curve.order - 1)
    pubkey = curve.ladder(privkey, curve.base)
    return privkey, pubkey


def points_from_sig(curve, pubkey, msg, sig):
    valid, Q = ecdsa_verify(curve, pubkey, msg, sig)
    if valid:
        return valid, Q, []

    QQ_list = curve.lift_x(sig[0])
    return valid, Q, QQ_list
    

SECP256R1 = {
    'name'   : 'secp256r1',
    'p'      : 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff,
    'order'  : 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551,
    'A'      : -3,
    'B'      : 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b,
    'x0'     : 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
    'y0'     : 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
}

SECP256K1 = {
    'name'  : 'secp256k1',
    'p'     : 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f,
    'order' : 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141,
    'A'     : 0,
    'B'     : 7,
    'x0'    : 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
    'y0'    : 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
}


SECP384R1 = {
    'name'   : 'secp384r1',
    'p'      : 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffeffffffff0000000000000000ffffffff,
    'order'  : 0xffffffffffffffffffffffffffffffffffffffffffffffffc7634d81f4372ddf581a0db248b0a77aecec196accc52973,
    'A'      : -3,
    'B'      : 0xb3312fa7e23ee7e4988e056be3f82d19181d9c6efe8141120314088f5013875ac656398d8a2ed19d2a85c8edd3ec2aef,
    'x0'     : 0xaa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab7,
    'y0'     : 0x3617de4a96262c6f5d9e98bf9292dc29f8f41dbd289a147ce9da3113b5f0b8c00a60b1ce1d7e819d7a431d7c90ea0e5f
}

CURVES = {
    'secp256r1' : SECP256R1,
    'secp256k1' : SECP256K1,
    'secp384r1' : SECP384R1
}

SCALAR_MULT_MODE = {
    'normal'   : scalar_mult_padding,
    'blinding' : scalar_mult_blinding,
    'multsplit': scalar_mult_splitting_mult,
    'euclsplit': scalar_mult_splitting_eucl
}

CURVE_TYPE = {
    'Jac': CurveJac,
    'XZ' : CurveXZ,
    'CoZ': CurveCoZ
}
