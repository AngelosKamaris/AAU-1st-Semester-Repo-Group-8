"""
Experiment: the simple time/storage attack.

Runs the honest prover and cheaters that keep only a share p of the table but brute-force whenever the answer is 
not stored. For each prover it prints:
  - how much it stores, compared with the honest prover,
  - how many challenges it passes (all of them: it never gives up),
  - the average and maximum hash calls per challenge.

Run from the PoSpace folder:
    python -m experiments.time_storage
    python -m experiments.time_storage --n-bits 12 --challenges 300
"""

from __future__ import annotations

import time, argparse

from pos import PoSParams, Verifier
from pos.cli import challenges_arg, n_bits_arg, seed_arg
from pos.schemes import SimpleScheme
from pos.provers import HonestProver, Prover, TimeStorageProver

FRACTIONS = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9]   # share of the table each cheater keeps


def run(prover: Prover, verifier: Verifier, challenges: int) -> dict:
    """Set up one prover, send it `challenges` challenges, and collect results."""
    prover.setup()
    setup_calls = prover.queries
    passed = 0
    seconds = 0.0
    max_calls = 0
    for _ in range(challenges):
        y = verifier.new_challenge()
        calls_before = prover.queries
        start = time.perf_counter()
        answer = prover.answer(y) # only the prover's work is timed
        seconds += time.perf_counter() - start
        max_calls = max(max_calls, prover.queries - calls_before)
        passed += verifier.check(y, answer)
    return {
        "prover": prover.name, "storage": prover.storage_bits(), "entries": len(prover.plot),
        "passed": passed / challenges, "calls": (prover.queries - setup_calls) / challenges, 
        "max_calls": max_calls, "ms": seconds / challenges * 1000,
    }

def print_results(results: list[dict], args: argparse.Namespace, N: int) -> None:
    """Print a table of results for several provers."""

    honest_storage = results[0]["storage"]
    print(f"\nTime/storage attack (N = 2^{args.n_bits} = {N}, {args.challenges} challenges each)\n")
    print(f"{'Prover':<26} {'Storage':>8} {'S (entries)':>10} {'Passed':>7} {'Avg calls':>10} "
          f"{'Max calls':>10} {'Call bound':>10} {'Avg time':>10}")
    print("-" * 77)
    for r in results:
        storage = f"{r['storage'] / honest_storage:.0%}"
        worst = N - r["entries"]
        print(f"{r['prover']:<26} {storage:>8} {r['entries']:>10} {r['passed']:>7.0%} "
              f"{r['calls']:>10.1f} {r['max_calls']:>10} {worst:>10} {r['ms']:>7.2f} ms")
        
    print("\nStorage is relative to the honest prover.")
    print("Avg calls = hash evaluations per challenge (setup excluded).")
    print("Max calls = the most hash calls any single challenge needed in this run.")
    print("Call bound = N - S; collisions can yield an earlier match.")
    print("Avg time = wall-clock time the prover needs to answer one challenge (depends on the machine).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Time/storage attack experiment")
    parser.add_argument("--n-bits", type=n_bits_arg, default=10, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", type=seed_arg, default=1, help="plot seed")
    parser.add_argument("--challenges", type=challenges_arg, default=200, help="challenges per prover")
    args = parser.parse_args()

    scheme = SimpleScheme(PoSParams(n_bits=args.n_bits, seed=args.seed))
    N = scheme.params.N

    provers = [HonestProver(scheme)]
    provers += [TimeStorageProver(scheme, p, rng_seed=args.seed) for p in FRACTIONS]

    # Every prover faces the same sequence of challenges (same verifier seed).
    results = [run(p, Verifier(scheme, rng_seed=args.seed), args.challenges) for p in provers]
    print_results(results, args, N)

if __name__ == "__main__":
    main()
