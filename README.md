# Differential Fault Attack Simulations on Montgomery Ladder

This repository contains simulations related to the paper *Differential Fault Attack on Montgomery Ladder and in the Presence of Scalar Randomization* that is to be presented at [INDOCRYPT 2021](https://indocrypt2021.lnmiit.ac.in/), the 22nd International Conference of Cryptography in India.

This is licensed under the terms of the [GNU General Public License v3](https://www.gnu.org/licenses/gpl-3.0.en.html).


## Invariant Sign-Change Fault Attack

In a Differential Fault Attack (DFA), the attacker disrupts the execution of a cryptographic calculation to find a secret key by comparing the effects of the fault on the output. 

The *Invariant Sign-Change Fault* described in the paper inverts the two elliptic curve points *R0* and *R1* that are manipulated in the elliptic curve scalar multiplication with the Montgomery ladder algorithm.
The impact of this fault is that the output *Q* of the scalar multiplication *Q=[k]P* (where *P* is the base point and *k* the secret scalar) is transformed in a point *Q'* such that their difference *Q−Q'* only depends on a few bits of the secret *k*, thus making it possible to find them.

In an ECDSA signature scheme, *k* is a random nonce and knowing a few bits of several nonces is sufficient to recover the private key with lattice methods.


## Content

Several simulations of the attack are presented here.
Those are arranged in three folders:

* `gdb/`: Simulations on OpenSSL with GDB, the GNU Debugger;
* `pysimul/`: Simulations in Python3, and includes the lattice attack to recover a private key;
* `unicorn/`: Simulations with Unicorn/Rainbow.

See the individual README files for specific instructions and documentation on each simulation.


## Requirements

Python version 3.6 at least is required for the use of f-strings.
Python version 3.8 at least is required for `math.isqrt` (a replacement is given in comments in the file `pysimul/pydfa/dfa_dl.py` if the requirement cannot be satisfied).

The lattice attack is dependent on the `fpylll` Python wrapper of the `fplll` library.
See the README file in the folder `pysimul`.

Consult the individual README files of each simulations for other specific requirements.
