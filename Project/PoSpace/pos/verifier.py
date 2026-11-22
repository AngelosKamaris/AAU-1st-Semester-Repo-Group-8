"""The verifier: issues challenges and checks answers and optional deadlines."""

from __future__ import annotations

import math
import random
from typing import Any, Optional

from pos.schemes.base import Scheme


class Verifier:
    """Uses OS-backed challenge randomness unless a test seed is explicitly given."""

    def __init__(
        self,
        scheme: Scheme,
        rng_seed: Optional[int] = None,
        max_response_time_ms: Optional[float] = None,
    ) -> None:
        if max_response_time_ms is not None:
            if isinstance(max_response_time_ms, bool) or not isinstance(
                max_response_time_ms, (int, float)
            ):
                raise ValueError(
                    "max_response_time_ms must be a finite number greater than 0"
                )
            try:
                valid_deadline = (
                    math.isfinite(max_response_time_ms) and max_response_time_ms > 0
                )
            except OverflowError:
                valid_deadline = False
            if not valid_deadline:
                raise ValueError(
                    "max_response_time_ms must be a finite number greater than 0"
                )
        self.scheme = scheme
        self.f = scheme.new_function()  # the verifier's own copy of f
        self.rng = (
            random.Random(rng_seed)
            if rng_seed is not None
            else random.SystemRandom()
        )
        self.max_response_time_ms = max_response_time_ms

    def new_challenge(self) -> int:
        """Pick a challenge y to send to the prover."""
        return self.scheme.sample_challenge(self.f, self.rng)

    def check(
        self, y: int, answer: Any, response_time_ms: Optional[float] = None
    ) -> bool:
        """Accept a valid answer returned within the configured deadline."""
        if self.max_response_time_ms is not None:
            if isinstance(response_time_ms, bool) or not isinstance(
                response_time_ms, (int, float)
            ):
                return False
            try:
                within_deadline = (
                    math.isfinite(response_time_ms)
                    and 0 <= response_time_ms <= self.max_response_time_ms
                )
            except OverflowError:
                within_deadline = False
            if not within_deadline:
                return False
        return self.scheme.is_valid(self.f, y, answer)
