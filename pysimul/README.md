# DFA Simulations with Python

This repository contains Python3 scripts to test the DFA attack presented in the paper *Differential Fault Attack on Montgomery Ladder and in the Presence of Scalar Randomization*.

Several cases are considered:
* A padding is applied on the scalar: *k* is replaced by *k + q* or *k + 2q* such that the padded scalar is one bit longer than the bit length of *q*;
* Randomization with the group order: *k* is replaced by *k + mq* where *q* is the group order and *m* a random integer;
* Randomization with the Euclidean splitting: *k* replaced by *a*, *m* and *b*, where *k = am + b* is the Euclidean division of *k* by a random integer *m*;
* Randomization with the multiplicative splitting: *k* is replaced by *m* and *γ* where *γ = k/m mod q* with *m* a random integer;
* Point addition formulas: classic version with projective Jacobian coordinates, *x*-only formulas, or *co-Z* Jacobian formulas.


## Content

The list of files and what they correspond is:

* `pydfa/`: several Python scripts;
  * `ec.py`: elliptic curve calculation (field finite field, formulas, scalar muliplication, blinding methods);
  * `dfa_dl.py`: Baby-Step Giant-Step algorithm to compute small discrete logarithm;
  * `dfa_analysis.py`: all functions to perform the DFA analysis on the different cases of the paper;
* `pysimul_skip_ecdsa_{normal,blinding,euclsplit,multsplit}.py`: scripts to launch a simulation of the attack on the swap for each case in the context of ECDSA;
* `pysimul_skip_fixed_multsplit.py`: same as above, but with a fixed scalar and the multiplicative splitting randomization method;
* `solve_hnp.py`: reconstruct a private key with lattice techniques;
* `results/`: this directory contains the resulting files of some of the above scripts that can be run with the `solve_hnp.py` script.


## Dependencies

The only dependency is `fpylll` for the script `solve_hnp.py` (all the other scripts only rely on built-in Python libraries).

We refer to [https://github.com/fplll/fpylll](https://github.com/fplll/fpylll) for installation of `fpylll` or use a [docker image](https://hub.docker.com/r/fplll/fpylll) for simplicity.


## Running the Simulations

### ECDSA without Blinding

The first case does not make use of blinding methods, only a padding is applied on the ephemeral scalar in the generation of an ECDSA signature.

The command is

```
python3 pysimul_skip_ecdsa_normal.py --curve <curve> --formulas <formulas> --skip <skip> --nsig <nsig> --fname <filename>
```

The arguments are
* `curve`: the name of the curve;
* `formulas`: one of `Jac`, `XZ`, `CoZ`;
* `skip`: step where the fault occurs;
* `nsig`: number of signatures;
* `fname`: name of the file to store the results to be used with the lattice attack.

An example is the command

```
python3 pysimul_skip_ecdsa_normal.py --curve secp256r1 --formulas Jac --skip 5 --nsig 150 --fname ecdsa_normal.txt
```

It will run calculation with the curve `secp256r1` using the Jacobian projective formulas, with a fault on step `j=5` and is repeated for 150 signatures.

At the start of the script a key pair private/public key is generated, then random messages are signed.
Once this is done, the DFA analysis is executed on the signatures and data for the lattice construction is written in the file `ecdsa_normal.txt`.


### ECDSA with Group Order Blinding

The scalar *k* is replaced by *k + mq* where *q* is the group order and *m* a random integer.

Running the simulation is essentially the same as above, except for the additional parameter `lambda` for the size in bits of the randomizer *m*.
The step where the fault occurs must be greater than `lambda`.

The command is

```
python3 pysimul_skip_ecdsa_blinding.py --curve <curve> --formulas <formulas> --skip <skip> --lambda <lambda> --nsig <nsig> --fname <filename>
```

An example is

```
python3 pysimul_skip_ecdsa_blinding.py --curve secp256r1 --formulas Jac --skip 25 --lambda 20 --nsig 150 --fname ecdsa_blinding.txt
```

In this case, the fault occurs on step *25* and the randomizer is *20* bits in length.
The resulting data will be similar as the case without blinding, but the DFA analysis requires the calculation of larger discrete logarithms which takes more time.


### ECDSA with Euclidean Splitting

The scalar *k* is rewritten *k = am + b* and the scalar multiplication is done in three parts, one for each of *a*, *m* and *b*.

As with the previous case, we need a parameter `lambda` to specify the size of the randomizer *m*.
However, all calculation are performed using the formulas `Jac` (the other formulas require a different analysis as there is a sign change, see Section 3.2 of the paper).

The cost of analysis is higher than the group order blinding method, so beware with large values of `lambda`.
On another hand, it requires much less signatures to recover a private key.

```
python3 pysimul_skip_ecdsa_euclsplit.py --curve <curve> --skip <skip> --lambda <lambda> --nsig <nsig> --fname <filename>
```

The step `skip` where the fault occurs must be less than `lambda` as the fault is made on the scalar multiplication with the randomizer of `lambda` bits.

An example is

```
python3 pysimul_skip_ecdsa_euclsplit.py --curve secp256r1 --skip 5 --lambda 16 --nsig 50 --fname ecdsa_euclsplit.txt
```


### ECDSA with Multiplicative Splitting

The scalar *k* is replaced by *m* and *γ* where *γ = k/m mod q* with *m* a random integer.

Again, there is a parameter `lambda` for the size of the randomizer *m*, and all calculations are performed using the `Jac` formulas.

The command is

```
python3 pysimul_skip_ecdsa_multsplit.py --curve <curve> --skip <skip> --lambda <lambda> --nsig <nsig> --fname <filename>
```

An example is

```
python3 pysimul_skip_ecdsa_multsplit.py --curve secp256r1 --skip 5 --lambda 16 --nsig 200 --fname ecdsa_multsplit.txt
```

We chose in this example a higher number of signatures because some can lead to several potential leaks and are discarded (see Section 4.3 of the paper).


### Running the Lattice Attack with the HNP Solver

In all the situations a file is created with the data to construct a lattice according to the construction given in Appendix A of the paper.

The structure of the file is as follows:

```
<curve name>,<x-coordinate public key>,<y-coordinate public key>
<u1>,<v1>,<L1>
<u2>,<v2>,<L2>
(...)
```

The first line contains the elliptic curve name followed by the coordinate of the public key (note that the private key is never kept).
Each of the following line corresponds to data derived from a signature and is used for the construction of the basis matrix of the lattice.

For all cases, it is only needed to run

```
python3 solve_hnp.py <filename>
```

The results of the commands given in the previous examples can be tested.
For instance, the case of the Euclidean splitting should give instantly the private key:

```
$ python3 solve_hnp.py results/ecdsa_euclsplit.txt
Elliptic curve: secp256r1
    Public key: (0x20acaeb0bdaa50a6e3d8b66f5a240d2adc4a4662543e918142a31b12e24b43e0,
                 0x7c6e4a30d81d73c2205ef8bdd93cedfe5a50e46b1dffc9a8176aaf76c1b2fe1a)
HNP with 17 signatures...
Private key: 19835340476999976169047096762670479373135307923046886600220536079106688612929
```

However, in the case of group order blinding, it should last a few seconds because only a few bits are known for nonce so it requires more signatures:

```
$ python3 solve_hnp.py results/ecdsa_blinding.txt 
Elliptic curve: secp256r1
    Public key: (0xf4cc068b8e3ba19e820beebc29f48c81080179ccacff954b9179a7d8649946b0,
                 0x53d900567829163fca1d2b57ae1fa44d86b489dc3b3bed28b99d872d1cd29c56)
HNP with 52 signatures...
HNP with 53 signatures...
Private key: 91606728301651811503926736983392768609401203008770568009220033835174464496115
```

