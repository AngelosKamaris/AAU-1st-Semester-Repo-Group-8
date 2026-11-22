"""Set up a prover and run the local proof-of-space demo."""

import time
from typing import Optional

from pos.provers import HonestProver, PartialStorageProver, Prover, TimeStorageProver
from pos.schemes.base import Scheme
from pos.verifier import Verifier

PROVERS = ("honest", "partial", "timestorage")
STAGE_2_CHALLENGES = 100
STAGE_2_DEADLINE_MS = 0.05


def build_prover(scheme: Scheme, name: str, fraction: float,
                 online_query_budget: Optional[int] = None) -> Prover:
    if name == "honest":
        return HonestProver(scheme)
    if name == "partial":
        return PartialStorageProver(scheme, fraction, rng_seed=scheme.params.seed)
    if name == "timestorage":
        return TimeStorageProver(scheme, fraction, scheme.params.seed, online_query_budget)
    raise ValueError(f"unknown prover {name}")


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


def run_trials(prover: Prover, verifier: Verifier, count: int, trials: int) -> int:
    deadline = verifier.max_response_time_ms
    if deadline is not None:
        print(f"Response limit: {deadline:g} ms per challenge")
    accepted_trials = valid_answers = attempted = 0
    response_seconds = verification_seconds = 0.0
    setup_calls = prover.queries
    verifier_calls = verifier.f.calls
    for trial in range(1, trials + 1):
        valid_count = 0
        for index in range(1, count + 1):
            challenge = verifier.new_challenge()
            calls_before = prover.queries
            start = time.perf_counter()
            answer = prover.answer(challenge)
            elapsed = time.perf_counter() - start
            elapsed_ms = elapsed * 1000
            response_seconds += elapsed
            start = time.perf_counter()
            valid = verifier.check(challenge, answer, response_time_ms=elapsed_ms)
            verification_seconds += time.perf_counter() - start
            valid_count += valid
            attempted += 1
            status = "accepted" if valid else "rejected"
            if deadline is not None and elapsed_ms > deadline:
                status = "timed out"
            work = prover.queries - calls_before
            print(f"  #{index:<3} y = {challenge:<8} answer = {answer!s:<8} {status:<9} "
                  f"({work} function calls, {elapsed_ms:.4f} ms)")
            if not valid:
                break
        valid_answers += valid_count
        accepted = valid_count == count
        accepted_trials += accepted
        status = "accepted" if accepted else "rejected"
        if not accepted and deadline is not None:
            status += " (classified as adversary)"
        print(f"Trial {trial}: {valid_count}/{count} required answers valid. Proof {status}")

    print(f"\nChallenges attempted: {attempted}/{count * trials}")
    print(f"Valid answers: {valid_answers}/{attempted} attempted ({valid_answers / attempted:.1%})")
    print(f"Trials accepted: {accepted_trials}/{trials} ({accepted_trials / trials:.1%})")
    print(f"Online prover evaluations: {prover.queries - setup_calls:,}")
    print(f"Verifier evaluations (including challenge generation): {verifier.f.calls - verifier_calls:,}")
    print(f"Total response time: {response_seconds * 1000:.4f} ms")
    print(f"Verification time: {verification_seconds * 1000:.4f} ms")
    return accepted_trials
