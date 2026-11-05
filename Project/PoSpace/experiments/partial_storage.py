"""Experiment: how well does the partial storage attack do?

Runs the honest prover and several cheaters (each keeping a different share
of the table) against the same verifier, and prints one row per prover:
  - how much they store, compared with the honest prover,
  - how many challenges they pass.

Run from the PoSpace folder:
    python -m experiments.partial_storage
    python -m experiments.partial_storage --n-bits 12 --challenges 300
"""

from __future__ import annotations

import argparse

from pos import PoSParams, Verifier
from pos.provers import HonestProver, PartialStorageProver, Prover
from pos.schemes import SimpleScheme

FRACTIONS = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9]   # share of the table each cheater keeps


def run(prover: Prover, verifier: Verifier, challenges: int) -> dict:
    """Set up one prover, send it `challenges` challenges, and collect results."""
    prover.setup()
    passed = 0
    for _ in range(challenges):
        y = verifier.new_challenge()
        passed += verifier.check(y, prover.answer(y))
    return {
        "prover": prover.name,
        "storage": prover.storage_bits(),
        "passed": passed / challenges,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Partial storage attack experiment")
    parser.add_argument("--n-bits", type=int, default=12, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", type=int, default=1, help="plot seed")
    parser.add_argument("--challenges", type=int, default=200, help="challenges per prover")
    args = parser.parse_args()

    scheme = SimpleScheme(PoSParams(n_bits=args.n_bits, seed=args.seed))
    N = scheme.params.N

    provers = [HonestProver(scheme)]
    provers += [PartialStorageProver(scheme, f, rng_seed=args.seed) for f in FRACTIONS]

    # Every prover faces the same sequence of challenges (same verifier seed).
    results = [run(p, Verifier(scheme, rng_seed=args.seed), args.challenges) for p in provers]

    honest_storage = results[0]["storage"]
    print(f"\nPartial storage attack (N = 2^{args.n_bits} = {N}, "
          f"{args.challenges} challenges each)\n")
    print(f"{'Prover':<24} {'Storage':>9} {'Passed':>9}")
    print("-" * 44)
    for r in results:
        storage = f"{r['storage'] / honest_storage:.0%}"
        print(f"{r['prover']:<24} {storage:>9} {r['passed']:>9.1%}")
    print("\nStorage is shown relative to the honest prover.")


if __name__ == "__main__":
    main()
