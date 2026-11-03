"""Experiment: how well does the partial storage attack do?

Runs the honest prover and several cheaters against the same verifier and
prints one row per prover:
  - how much they store,
  - how many challenges they pass,
  - how much work (hash calls) they do per challenge.

Run from the PoSpace folder:
    python -m experiments.partial_storage
    python -m experiments.partial_storage --n-bits 12 --challenges 300
"""

from __future__ import annotations

import argparse

from pos import PoSParams, Verifier
from pos.provers import HonestProver, PartialStorageProver, Prover
from pos.schemes import SimpleScheme

FRACTIONS = [0.0, 0.25, 0.5, 0.75]       # share of the table the cheater keeps
BUDGET_SHARES = [0.0, 0.1, 0.5, 1.0]     # brute-force budget, as a share of N


def run(prover: Prover, verifier: Verifier, challenges: int) -> dict:
    """Set up one prover, send it `challenges` challenges, and collect results."""
    prover.setup()
    setup_calls = prover.queries
    passed = 0
    for _ in range(challenges):
        y = verifier.new_challenge()
        passed += verifier.check(y, prover.answer(y))
    return {
        "prover": prover.name,
        "storage": prover.storage_bits(),
        "passed": passed / challenges,
        "work": (prover.queries - setup_calls) / challenges,
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
    for fraction in FRACTIONS:
        for share in BUDGET_SHARES:
            provers.append(PartialStorageProver(
                scheme, fraction, compute_budget=int(share * N), rng_seed=args.seed))

    # Every prover faces the same sequence of challenges (same verifier seed).
    results = [run(p, Verifier(scheme, rng_seed=args.seed), args.challenges) for p in provers]

    honest_storage = results[0]["storage"]
    print(f"\nPartial storage attack (N = 2^{args.n_bits} = {N}, "
          f"{args.challenges} challenges each)\n")
    print(f"{'Prover':<36} {'Storage':>9} {'Passed':>8} {'Hash calls/challenge':>22}")
    print("-" * 78)
    for r in results:
        storage = f"{r['storage'] / honest_storage:.0%}"
        print(f"{r['prover']:<36} {storage:>9} {r['passed']:>8.1%} {r['work']:>22,.1f}")
    print("\nStorage is shown relative to the honest prover.")


if __name__ == "__main__":
    main()
