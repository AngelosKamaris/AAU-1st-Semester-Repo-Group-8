"""
Attack 1: partial storage.

The cheater builds the full table during setup, keeps only `fraction` of it
(e.g. 50% or 25%), and throws the rest away to save space.

When challenged, it looks y up in the part it kept:
  - if the answer is there, it replies instantly;
  - if not, it has no answer and fails that challenge.

So a cheater that keeps a fraction p of the table should pass about p of the
challenges, while using only p of the honest prover's space.
"""

from __future__ import annotations

import random
from typing import Any, Optional

from pos.plot import Plot
from pos.provers.base import Prover
from pos.schemes.base import Scheme


class PartialStorageProver(Prover):
    def __init__(self, scheme: Scheme, fraction: float, rng_seed: Optional[int] = None) -> None:
        super().__init__(scheme)
        # Reject bool/str/None/nan/out-of-range
        if (isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or not 0.0 <= fraction <= 1.0):
            raise ValueError(f"fraction must be a number between 0 and 1, got {fraction!r}")
        self.fraction = fraction
        self.rng = random.Random(rng_seed)  # decides which entries are kept
        self.name = f"partial({fraction:.0%} stored)"

    def setup(self) -> None:
        full_plot = self.scheme.build_plot(self.f)
        self.plot: Plot = full_plot.random_subset(self.fraction, self.rng)

    def answer(self, y: int) -> Optional[Any]:
        return self.plot.lookup(y)   # None if this entry was thrown away

    def storage_bits(self) -> int:
        return self.plot.storage_bits()
