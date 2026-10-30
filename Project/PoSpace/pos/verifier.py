"""The verifier: issues a challenge and checks the answer.

No security measures yet: one challenge at a time, no time limit.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from pos.schemes.base import Scheme


class Verifier:
    def __init__(self, scheme: Scheme, rng_seed: Optional[int] = None) -> None:
        self.scheme = scheme
        self.f = scheme.new_function()  # the verifier's own copy of f
        self.rng = random.Random(rng_seed)

    def new_challenge(self) -> int:
        """Pick a challenge y to send to the prover."""
        return self.scheme.sample_challenge(self.f, self.rng)

    def check(self, y: int, answer: Any) -> bool:
        """Accept if the answer solves the challenge."""
        return self.scheme.is_valid(self.f, y, answer)
