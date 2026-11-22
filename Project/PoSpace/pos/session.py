"""Set up a prover and run the local proof-of-space demo."""

import time

from pos.provers import HonestProver, PartialStorageProver, Prover, TimeStorageProver
from pos.schemes.base import Scheme
from pos.verifier import Verifier

PROVERS = {
    "honest": HonestProver,
    "partial": PartialStorageProver,
    "timestorage": TimeStorageProver,
}


def build_prover(scheme: Scheme, name: str, fraction: float) -> Prover:
    if name == "honest":
        return HonestProver(scheme)
    return PROVERS[name](scheme, fraction, rng_seed=scheme.params.seed)


def initialize(prover: Prover) -> None:
    start = time.perf_counter()
    prover.setup()
    setup_seconds = time.perf_counter() - start
    params = prover.scheme.params
    print(f"Prover: {prover.name}")
    print(f"Initialization (N = 2^{params.n_bits} = {params.N}, function = blake2b)")
    print(f"  table entries:     {len(prover.plot)}")
    print(f"  plot storage:      {(prover.plot.storage_bits() + 7) // 8:,} packed bytes")
    print(f"  storage:           {prover.storage_bits():,} bits")
    if isinstance(prover, HonestProver):
        print(f"  distinct outputs:  {len(prover.plot):,}")
        print(f"  collisions:        {params.N - len(prover.plot):,}")
    print(f"  setup evaluations: {prover.queries:,}")
    print(f"  setup time:        {setup_seconds:.3f} s")


def run_trials(prover: Prover, verifier: Verifier, trials: int) -> None:
    print("\nChallenges")
    accepted = 0
    verification_seconds = 0.0
    setup_calls = prover.queries
    for index in range(1, trials + 1):
        challenge = verifier.new_challenge()
        calls_before = prover.queries
        start = time.perf_counter()
        answer = prover.answer(challenge)
        elapsed = time.perf_counter() - start
        work = prover.queries - calls_before
        start = time.perf_counter()
        valid = verifier.check(challenge, answer)
        verification_seconds += time.perf_counter() - start
        accepted += valid
        status = "accepted" if valid else "rejected"
        print(f"  #{index:<3} y = {challenge:<8} answer = {answer!s:<8} {status:<9} "
              f"({work} function calls, {elapsed * 1000:.4f} ms)")

    answer_calls = prover.queries - setup_calls
    print(f"\nValid answers: {accepted}/{trials} ({accepted / trials:.1%})")
    print(f"Average function calls per challenge: {answer_calls / trials:,.1f}")
    print(f"Verification time: {verification_seconds * 1000:.4f} ms")
