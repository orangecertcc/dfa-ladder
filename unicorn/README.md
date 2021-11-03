# DFA Simulation with Unicorn Emulator

This repository contains files to test the DFA attack presented in the paper *Differential Fault Attack on Montgomery Ladder and in the Presence of Scalar Randomization* using the Unicorn Emulator through the tool [Rainbow](https://github.com/Ledger-Donjon/rainbow/).

These simulations allow to check the effects a skip of an instruction during a scalar multiplication with the Montgomery ladder algorithm, either with the classic formulas with Jacobian coordinates, or with the *co-Z* formulas.

With fixed inputs, it is possible to get the results for different instructions skipped: the output point, its validity, and the results of the analysis of the *Invariant Sign-Change Fault* attack.


## Content

This folder contains the following files:

* `binaries`: C source files for binaries that implement the scalar multiplication with the Montgomery ladder algorithm and different point addition formulas;
* `unicorn_simul_{jac,coz}.py`: Python3 scripts that run the Unicorn simulation


## Requirements

The fault injection simulations on the binaries rely only on `Rainbow`, a tool based on the `Unicorn` engine.

A setup installation is given in https://github.com/Ledger-Donjon/rainbow/.


## Compilation of the Binaries

The two binaries are based on the efficient big integer arithmetic of curve `secp256r1` for architecture *x86_64*.

It is as simple as `make` to produce them from the source files.

The binaries are called `ladderjac` and `laddercoz` and both compute a scalar multiplication with the Montgomery ladder algorithm.
The input is a scalar given as a string of 64 hexadecimal charaters exactly, and the result is appended as a new line in the file `output.txt` in the format `<scalar>,<x>,<y>` where *(x,y)* is the resulting point.

Remark: the Unicorn emulator works by calling directly the function with the proper inputs and does not go through the main function of the binaries.


## Running the Simulations

Those simulations use the skip instruction fault model with the `secp256r1` curve.
A padding on the scalar is applied before the scalar multiplication.


### Montgomery Ladder with Jacobian XYZ Formulas

The command is

```
python3 unicorn_simul_jac.py --scalar <scalar> --inst <instruction number> --width <width> --skip <min> <max>
```

The arguments are
* `scalar`: a scalar of 256 bits at most;
* `inst`: number of the instruction in the whole scalar multiplication;
* `width`: many scalar multiplication will be made with an instruction skipped in the interval *[inst - width, inst + width]*;
* `skip`: for the analysis, makes the hypothesis that fault occured between steps 'min' and 'max'.

An example is given by the following command:

```
python3 unicorn_simul_jac.py --scalar 45349009246906155976193524215960074469545443595901196458833407743122392196045 --inst 1105339 --width 0 --skip 18 18
```

The skipped instruction is `pbit <- pbit XOR k_i` during the processing the bit *k<sub>17</sub>* of the scalar, thus impacting the last 18 bits of the scalar, so the options of the argument `skip` are "18 18" and the result is:

```
Instruction skipped: (5263, 2, 'xor', 'ebp, eax')
  Output  : (f108216114fac79a408ceacfdfc8a51f3fe296427794f48ea654011eb3e1a1be,b29e858ecd39497da6dec5e02be62a13d6c70533c113648eb1c18f504a872b8a)
  On curve: True
  # Q'    : 2
  Found   : 182558  kpad mod 2^18: 182558
  Reduced : 182558  kpad mod 2^18: 182558
```

Instead, if the argument `skip` is "15 20" then it broadens the search (for the least significant bits of the scalar) and the result is reduced *mod 2<sup>15</sup>*:

```
Instruction skipped: (5263, 2, 'xor', 'ebp, eax')
  Output  : (f108216114fac79a408ceacfdfc8a51f3fe296427794f48ea654011eb3e1a1be,b29e858ecd39497da6dec5e02be62a13d6c70533c113648eb1c18f504a872b8a)
  On curve: True
  # Q'    : 2
  Found   : 575774  kpad mod 2^20: 182558
  Reduced : 18718  kpad mod 2^15: 18718
```

To look at the effects of a skip of a different instruction surrounding the desired one, one can use the argument `width` by setting a positive value.
For example with `--width 5`, we obtain the false positive of the paper (which can be discarded) and the other instruction that makes the attack work (`pbit <- k_i`):

```
python3 unicorn_simul_jac.py --scalar 45349009246906155976193524215960074469545443595901196458833407743122392196045 --inst 1105339 --width 5 --skip 15 20
```

The instructions that correspond to the line `pbit <- pbit XOR k_i` for the last 20 bits of the scalar are:

```
[1096073, 1100706, 1105339, 1109972, 1114605, 1119238, 1123871, 1128504, 1133137, 1137770, 1142403, 1147036, 1151669, 1156302, 1160935, 1165568, 1170201, 1174834, 1179467, 1184100]
```


### Montgomery Ladder with XYcoZ Formulas

The command is similar but it has an additional argument for the initial value for the *Z*-coordinate of the points for randomization.

```
python3 unicorn_simul_coz.py --scalar <scalar> --initZ <initial_Z> --inst <inst> --width <width> --skip <min> <max>
```

The instructions that correspond to the line `pbit <- pbit XOR k_i` for the last 20 bits of the scalar are:

```
[774554, 777820, 781086, 784352, 787618, 790884, 794150, 797416, 800682, 803948, 807214, 810480, 813746, 817012, 820278, 823544, 826810, 830076, 833342, 836608]
```

An example that targets the processing of the bit *k<sub>17</sub>* is:

```
python3 unicorn_simul_coz.py --scalar 45349009246906155976193524215960074469545443595901196458833407743122392196045 --initZ 9804507658142387508622287579781258972417378912574071646772754339370875346659 --inst 781086 --width 0 --skip 18 18
```

And the result is

```
Instruction skipped: (6835, 2, 'xor', 'ebx, eax')
  Output  : (f108216114fac79a408ceacfdfc8a51f3fe296427794f48ea654011eb3e1a1be,4d617a7132c6b68259213a1fd519d5ec2938facc3eec9b714f3e70afb478d475)
  On curve: True
  # Q'    : 2
  Found   : 182558  kpad mod 2^18: 182558
  Reduced : 182558  kpad mod 2^18: 182558
```

