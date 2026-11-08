"""Run the proof of space: initialization, then challenges.

Examples:
    python main.py                                         # honest prover
    python main.py --n-bits 12 --challenges 20 --seed 42
    python main.py --prover partial --fraction 0.5         # cheater keeps 50%
    python main.py --prover partial --fraction 0.25        # cheater keeps 25%
    python main.py --prover timestorage --fraction 0.5     # keeps 50%, brute-forces the rest
"""

from __future__ import annotations

import time, argparse

from pos import PoSParams, Verifier
from pos.cli import challenges_arg, fraction, master_key_arg, n_bits_arg, rounds_arg, seed_arg
from pos.provers import HonestProver, PartialStorageProver, TimeStorageProver
from pos.schemes import SimpleScheme

PROVER_ARGS = ["honest", "partial", "timestorage"]

def build_prover(args, scheme):
    """Create the prover chosen on the command line."""
    if args.prover == "honest": return HonestProver(scheme)
    if args.prover == "partial": return PartialStorageProver(scheme, fraction=args.fraction, rng_seed=args.seed)
    if args.prover == "timestorage": return TimeStorageProver(scheme, fraction=args.fraction, rng_seed=args.seed)
    raise ValueError(f"unknown prover {args.prover}")


def short(y: int) -> str:
    """Shorten long challenge values for readable output."""
    value = f"{y:x}"
    return value if len(value) <= 12 else value[:12] + "..."


def main() -> None:
    parser = argparse.ArgumentParser(description="Proof of space demo")
    parser.add_argument("--n-bits", type=n_bits_arg, default=16, help="domain size N = 2^n_bits")
    parser.add_argument("--function", choices=("feistel", "blake2b"), default="feistel")
    parser.add_argument("--rounds", type=rounds_arg, default=8, help="Feistel rounds")
    parser.add_argument("--master-key", type=master_key_arg, help="repeatable Feistel key (32 hex characters)")
    parser.add_argument("--seed", type=seed_arg, default=1, help="challenge/attack random seed")
    parser.add_argument("--challenges", type=challenges_arg, default=1, help="number of challenges") 
    parser.add_argument("--prover", choices=PROVER_ARGS, default="honest", help="which prover to run")
    parser.add_argument("--fraction", type=fraction, default=0.5, help="partial/timestorage prover: share of the table it keeps (0 to 1)")
    args = parser.parse_args()

    if args.function == "feistel" and (args.n_bits < 2 or args.n_bits % 2):
        parser.error("Feistel requires an even --n-bits value of at least 2")
    if args.function != "feistel" and args.master_key is not None:
        parser.error("--master-key can only be used with Feistel")

    scheme = SimpleScheme(PoSParams(
        n_bits=args.n_bits,
        seed=args.seed,
        function=args.function,
        rounds=args.rounds,
        master_key=args.master_key,
    ))
    prover = build_prover(args, scheme)
    verifier = Verifier(scheme, rng_seed=args.seed)

    # Step 1: initialization
    start = time.perf_counter()
    prover.setup()
    setup_seconds = time.perf_counter() - start
    setup_calls = prover.queries
    print(f"Prover: {prover.name}")
    print(f"Initialization (N = 2^{args.n_bits} = {scheme.params.N}, function = {args.function})")
    if args.function == "feistel":
        print(f"  Feistel rounds:    {args.rounds}")
    print(f"  table entries:     {len(prover.plot)}")
    print(f"  storage:           {prover.storage_bits():,} bits")
    print(f"  setup evaluations: {setup_calls:,}")
    print(f"  setup time:        {setup_seconds:.3f} s")

    # Step 2: proof of execution
    print("\nChallenges")
    accepted = []
    for i in range(1, args.challenges + 1):
        y = verifier.new_challenge()
        calls_before = prover.queries
        start = time.perf_counter()
        answer = prover.answer(y)
        elapsed = time.perf_counter() - start        # time the prover needed to answer
        work = prover.queries - calls_before
        ok = verifier.check(y, answer)
        accepted.append(ok)
        print(f"  #{i:<3} y = {short(y)}  answer x = {answer!s:<8} {'accepted' if ok else 'rejected':<9} ({work} function calls, {elapsed * 1000:.2f} ms)")

    answer_calls = prover.queries - setup_calls
    print(f"\nValid answers: {sum(accepted)}/{args.challenges}")
    print(f"Proof {'accepted' if all(accepted) else 'rejected'}")
    print(f"Average function calls per challenge: {answer_calls / args.challenges:,.1f}")


if __name__ == "__main__":
    main()
