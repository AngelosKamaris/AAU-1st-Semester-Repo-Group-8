"""Run the basic proof of space: initialization, then challenges.

Examples:
    python main.py
    python main.py --n-bits 12 --challenges 20 --seed 42
"""

from __future__ import annotations

import argparse

from pos import PoSParams, Verifier
from pos.provers import HonestProver
from pos.schemes import SimpleScheme


def main() -> None:
    parser = argparse.ArgumentParser(description="Basic proof of space demo")
    parser.add_argument("--n-bits", type=int, default=8, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", type=int, default=1, help="plot seed")
    parser.add_argument("--challenges", type=int, default=10, help="number of challenges")
    args = parser.parse_args()

    scheme = SimpleScheme(PoSParams(n_bits=args.n_bits, seed=args.seed))
    prover = HonestProver(scheme)
    verifier = Verifier(scheme, rng_seed=args.seed)

    # Step 1: initialization
    prover.setup()
    print(f"Initialization (N = 2^{args.n_bits} = {scheme.params.N}, seed = {args.seed})")
    print(f"  table entries:     {len(prover.plot)}")
    print(f"  storage:           {prover.storage_bits():,} bits")
    print(f"  setup evaluations: {prover.queries:,}")

    # Step 2: proof of execution
    print(f"\nChallenges")
    accepted = 0
    for i in range(1, args.challenges + 1):
        y = verifier.new_challenge()
        answer = prover.answer(y)
        ok = verifier.check(y, answer)
        accepted += ok
        print(f"  #{i:<3} y = {y:<8} answer x = {answer!s:<8} {'accepted' if ok else 'rejected'}")

    print(f"\nAccepted {accepted}/{args.challenges}")


if __name__ == "__main__":
    main()
