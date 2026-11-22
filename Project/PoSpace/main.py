"""Run the proof of space: initialization, then challenges.

Examples:
    python main.py                                         # honest prover
    python main.py --n-bits 12 --challenges 20 --seed 42
    python main.py --prover partial --fraction 0.5         # cheater keeps 50%
    python main.py --prover partial --fraction 0.25        # cheater keeps 25%
    python main.py --prover timestorage --fraction 0.5     # keeps 50%, brute-forces the rest
"""

from __future__ import annotations

import argparse

from pos import PoSParams, Verifier
from pos.cli import (
    challenges_arg, fraction, int_in_range, n_bits_arg, positive_milliseconds, seed_arg,
)
from pos.schemes import SimpleScheme
from pos.session import (
    PROVERS, STAGE_2_CHALLENGES, STAGE_2_DEADLINE_MS, build_prover, initialize, run_trials,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Proof of space demo")
    parser.add_argument("--stage", type=int, choices=(1, 2), default=2)
    parser.add_argument("--n-bits", type=n_bits_arg, default=16, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", "--seed-f", type=seed_arg, default=1, help="public plot seed")
    parser.add_argument("--challenge-seed", type=seed_arg, help="optional seed for repeatable challenge sampling")
    parser.add_argument("--challenges", type=challenges_arg,
                        help=f"challenges per trial (Stage 2 default: {STAGE_2_CHALLENGES})")
    parser.add_argument("--trials", type=challenges_arg, default=1, help="number of independent trials")
    parser.add_argument("--time-limit-ms", type=positive_milliseconds,
                        help=f"Stage 2 response deadline (default: {STAGE_2_DEADLINE_MS:g} ms)")
    parser.add_argument("--online-query-budget", type=int_in_range(0), help="maximum search evaluations per missed lookup")
    parser.add_argument("--prover", choices=PROVERS, default="honest", help="which prover to run")
    parser.add_argument("--fraction", type=fraction, default=0.5, help="partial/timestorage prover: share of the table it keeps (0 to 1)")
    args = parser.parse_args()

    count = args.challenges or (1 if args.stage == 1 else STAGE_2_CHALLENGES)
    if args.stage == 1 and (count != 1 or args.time_limit_ms is not None):
        parser.error("Stage 1 uses one untimed challenge per trial; use --trials to repeat it")
    deadline = (args.time_limit_ms or STAGE_2_DEADLINE_MS) if args.stage == 2 else None

    scheme = SimpleScheme(PoSParams(n_bits=args.n_bits, seed=args.seed))
    prover = build_prover(scheme, args.prover, args.fraction, args.online_query_budget)
    verifier = Verifier(scheme, rng_seed=args.challenge_seed, max_response_time_ms=deadline)
    initialize(prover)
    print(f"\nStage {args.stage}: {count} required challenges per trial")
    if not run_trials(prover, verifier, count, args.trials) and args.trials == 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
