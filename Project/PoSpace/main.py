"""Command-line demo for the three proof-of-space stages."""

from __future__ import annotations

import argparse

from pos import PoSParams, Verifier
from pos.cli import (
    challenges_arg, fraction, int_in_range, n_bits_arg, positive_milliseconds, seed_arg,
)
from pos.schemes import SimpleScheme
from pos.schemes.paired import PairedScheme
from pos.session import (
    PROVERS, STAGE_2_CHALLENGES, STAGE_2_DEADLINE_MS, build_prover, initialize, run_trials,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Proof of space demo")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--n-bits", type=n_bits_arg, default=16, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", "--seed-f", type=seed_arg, default=1, help="public plot seed")
    parser.add_argument("--seed-g", type=seed_arg, default=2, help="public seed for Stage 3 pair hashing")
    parser.add_argument("--challenge-seed", type=seed_arg, help="optional seed for repeatable challenge sampling")
    parser.add_argument("--challenges", type=challenges_arg,
                        help=f"challenges per trial (Stage 2 default: {STAGE_2_CHALLENGES})")
    parser.add_argument("--threshold", "--acceptance-threshold", type=challenges_arg,
                        help="minimum valid answers per Stage 3 trial")
    parser.add_argument("--trials", type=challenges_arg, default=1, help="number of independent trials")
    parser.add_argument("--time-limit-ms", type=positive_milliseconds,
                        help=f"response deadline (Stage 2 default: {STAGE_2_DEADLINE_MS:g} ms)")
    parser.add_argument("--online-query-budget", type=int_in_range(0), help="maximum search evaluations per missed lookup")
    parser.add_argument("--prover", choices=PROVERS, default="honest", help="which prover to run")
    parser.add_argument("--fraction", type=fraction, default=0.5, help="partial/timestorage prover: share of the table it keeps (0 to 1)")
    args = parser.parse_args()

    count = args.challenges or (1, STAGE_2_CHALLENGES, 10)[args.stage - 1]
    if args.stage == 1 and (count != 1 or args.time_limit_ms is not None):
        parser.error("Stage 1 uses one untimed challenge per trial; use --trials to repeat it")
    if args.threshold is not None and (args.stage != 3 or args.threshold > count):
        parser.error("--threshold is only available in Stage 3 and cannot exceed --challenges")
    deadline = (args.time_limit_ms or STAGE_2_DEADLINE_MS) if args.stage == 2 else args.time_limit_ms

    scheme_type = PairedScheme if args.stage == 3 else SimpleScheme
    scheme = scheme_type(PoSParams(n_bits=args.n_bits, seed=args.seed, seed_g=args.seed_g))
    prover = build_prover(scheme, args.prover, args.fraction, args.online_query_budget)
    verifier = Verifier(scheme, rng_seed=args.challenge_seed, max_response_time_ms=deadline)
    initialize(prover)
    require_all = args.stage != 3
    rule = "require all" if require_all else (
        "coverage only" if args.threshold is None else f"threshold {args.threshold}"
    )
    print(f"\nStage {args.stage}: {count} challenges per trial ({rule})")
    accepted = run_trials(prover, verifier, count, args.trials, require_all=require_all, threshold=args.threshold)
    if accepted == 0 and args.trials == 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
