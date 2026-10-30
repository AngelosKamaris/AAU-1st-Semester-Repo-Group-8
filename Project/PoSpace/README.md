# Proof of Space: basic implementation

The simplest proof of space, with no security measures yet: a prover stores a
table, a verifier sends challenges and checks the answers.

## Run it

Python 3.9+, standard library only.

```bash
python main.py                                  # N = 2^8, 10 challenges
python main.py --n-bits 12 --challenges 20      # bigger table, more challenges
python -m unittest discover tests               # run the tests
```

## How it works

**Initialization**
- The function is f(x) = BLAKE2b(seed, x) mod N, with N = 2^n_bits.
- The prover computes f(x) for every x in [0, N) and stores a table y -> x.

**Proof of execution**
1. The verifier picks a random x and sends the challenge y = f(x).
2. The prover looks up y in its table and sends back an x' with f(x') = y.
3. The verifier computes f(x') and accepts if it equals y.

## Files

```
pos/
  params.py         PoSParams: n_bits (N = 2^n_bits) and the plot seed
  functions.py      HashFunction: f(x) = BLAKE2b(seed, x) mod N, counts its calls
  plot.py           Plot: the stored table (y -> x), reports its size in bits
  schemes/
    base.py         Scheme interface: build plot, pick challenge, check answer
    simple.py       The simple scheme described above
  provers/
    base.py         Prover interface: setup(), answer(y), storage_bits()
    honest.py       Honest prover: full table, answers by lookup
  verifier.py       Verifier: new_challenge(), check(y, answer)
main.py             Demo: initialization + challenges
tests/              unittest tests
```

## Extending it later

- **An attack** is a new `Prover` subclass in `pos/provers/`.
- **A new construction** (e.g. the collision-based g_f) is a new `Scheme`
  subclass in `pos/schemes/`.
- **Security measures** (repeated challenges, time limits) go in `verifier.py`.

## Notes

- **Honest storage is about 63% of N entries, not N.** A random function
  misses about 37% of outputs, so there are fewer distinct y values than x values.
- **The prover doesn't send the seed.** The verifier already knows which plot
  it's checking.
- **Every function object counts its evaluations** (`calls`). That will let us
  measure the work an attacker does later.
