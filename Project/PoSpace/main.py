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
from pos.cli import challenges_arg, fraction, n_bits_arg, seed_arg
from pos.schemes import SimpleScheme
from pos.session import PROVERS, build_prover, initialize, run_trials


def main() -> None:
    parser = argparse.ArgumentParser(description="Proof of space demo")
    parser.add_argument("--n-bits", type=n_bits_arg, default=16, help="domain size N = 2^n_bits")
    parser.add_argument("--seed", "--seed-f", type=seed_arg, default=1, help="public plot seed")
    parser.add_argument("--challenge-seed", type=seed_arg, help="optional seed for repeatable challenge sampling")
    parser.add_argument("--challenges", type=challenges_arg, default=1, help="number of independent single-challenge trials")
    parser.add_argument("--prover", choices=PROVERS, default="honest", help="which prover to run")
    parser.add_argument("--fraction", type=fraction, default=0.5, help="partial/timestorage prover: share of the table it keeps (0 to 1)")
    args = parser.parse_args()

    scheme = SimpleScheme(PoSParams(n_bits=args.n_bits, seed=args.seed))
    prover = build_prover(scheme, args.prover, args.fraction)
    verifier = Verifier(scheme, rng_seed=args.challenge_seed)
    initialize(prover)
    run_trials(prover, verifier, args.challenges)


if __name__ == "__main__":
    main()
