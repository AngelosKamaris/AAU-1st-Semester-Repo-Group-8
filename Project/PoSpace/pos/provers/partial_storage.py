"""Attack 1: partial storage, with brute force as a fallback.

The cheater builds the full table during setup, keeps only `fraction` of it,
and throws the rest away to save space. When challenged:
  1. If the answer is in the part it kept, look it up (instant).
  2. Otherwise, try x = 0, 1, 2, ... for up to `compute_budget` evaluations.

The two settings cover the whole range between storing and computing:
  fraction=1.0, budget=0  -> same as the honest prover
  fraction=0.0, budget=0  -> stores nothing, does nothing (always fails)
  fraction=0.0, budget=N  -> pure brute force: stores nothing, computes everything
  anything in between     -> stores some, computes some
"""

from __future__ import annotations

import random
from typing import Any, Optional

from pos.plot import Plot
from pos.provers.base import Prover
from pos.schemes.base import Scheme


class PartialStorageProver(Prover):
    def __init__(
        self,
        scheme: Scheme,
        fraction: float,
        compute_budget: int = 0,
        rng_seed: Optional[int] = None,
    ) -> None:
        super().__init__(scheme)
        self.fraction = fraction
        self.compute_budget = compute_budget
        self.rng = random.Random(rng_seed)  # decides which entries are kept
        self.name = f"partial({fraction:.0%} stored, budget {compute_budget})"

    def setup(self) -> None:
        full_plot = self.scheme.build_plot(self.f)
        self.plot: Plot = full_plot.random_subset(self.fraction, self.rng)

    def answer(self, y: int) -> Optional[Any]:
        stored = self.plot.lookup(y)
        if stored is not None:
            return stored
        if self.compute_budget > 0:
            return self.scheme.brute_force(self.f, y, self.compute_budget)
        return None

    def storage_bits(self) -> int:
        return self.plot.storage_bits()
