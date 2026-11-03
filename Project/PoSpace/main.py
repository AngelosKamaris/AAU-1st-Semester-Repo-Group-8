"""Run the proof of space: initialization, then challenges.

Examples:
    python main.py                                         # honest prover
    python main.py --n-bits 12 --challenges 20 --seed 42
    python main.py --prover partial --fraction 0.5         # cheater keeps 50%
    python main.py --prover partial --fraction 0.5 --budget 100
"""

from __future__ import annotations

import argparse

from pos import PoSParams, Verifier
from pos.provers import HonestProver, PartialStorageProver
from pos.schemes import SimpleScheme


def build_prover(args, scheme):
    """Create the prover chosen on the command line."""
    if args.prover == "honest":
        return HonestProver(scheme)
    if args.prover == "partial":
        return PartialStorageProver(
            scheme, fraction=args.fraction, compute_budget=args.budget, rng_seed=args.seed
        )
    raise ValueError(f"unknown prover {args.prover}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Proof of space demo")
    parser.add_argument("--n-bits", type=int, default=8, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", type=int, default=1, help="plot seed")
    parser.add_argument("--challenges", type=int, default=10, help="number of challenges")
    parser.add_argument("--prover", choices=["honest", "partial"], default="honest",
                        help="which prover to run")
    parser.add_argument("--fraction", type=float, default=0.5,
                        help="partial prover: share of the table it keeps (0 to 1)")
    parser.add_argument("--budget", type=int, default=0,
                        help="partial prover: max hash calls per challenge for brute force")
    args = parser.parse_args()

    scheme = SimpleScheme(PoSParams(n_bits=args.n_bits, seed=args.seed))
    prover = build_prover(args, scheme)
    verifier = Verifier(scheme, rng_seed=args.seed)

    # Step 1: initialization
    prover.setup()
    setup_calls = prover.queries
    print(f"Prover: {prover.name}")
    print(f"Initialization (N = 2^{args.n_bits} = {scheme.params.N}, seed = {args.seed})")
    print(f"  table entries:     {len(prover.plot)}")
    print(f"  storage:           {prover.storage_bits():,} bits")
    print(f"  setup evaluations: {setup_calls:,}")

    # Step 2: proof of execution
    print("\nChallenges")
    accepted = 0
    for i in range(1, args.challenges + 1):
        y = verifier.new_challenge()
        calls_before = prover.queries
        answer = prover.answer(y)
        work = prover.queries - calls_before
        ok = verifier.check(y, answer)
        accepted += ok
        print(f"  #{i:<3} y = {y:<8} answer x = {answer!s:<8} "
              f"{'accepted' if ok else 'rejected':<9} ({work} hash calls)")

    answer_calls = prover.queries - setup_calls
    print(f"\nAccepted {accepted}/{args.challenges}")
    print(f"Average hash calls per challenge: {answer_calls / args.challenges:,.1f}")


if __name__ == "__main__":
    main()
