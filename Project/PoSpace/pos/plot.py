"""The table a prover stores (the "plot")."""

from __future__ import annotations

import random
from typing import Any, Dict, Optional


class Plot:
    """A lookup table from challenge value y to an answer.

    The paper describes the table as "sorted by output" so lookups are fast.
    A Python dict gives the same fast lookup, so we use one.

    entry_bits is how many bits one stored entry costs, used to report storage.
    """

    def __init__(self, entries: Dict[int, Any], entry_bits: int) -> None:
        self._entries = entries
        self.entry_bits = entry_bits

    def lookup(self, y: int) -> Optional[Any]:
        """Return the stored answer for y, or None if we don't have one."""
        return self._entries.get(y)

    def __len__(self) -> int:
        return len(self._entries)

    def storage_bits(self) -> int:
        return len(self._entries) * self.entry_bits

    def random_subset(self, fraction: float, rng: random.Random) -> "Plot":
        """Keep a random `fraction` of the entries (used by cheating provers)."""
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("fraction must be between 0 and 1")
        keys = list(self._entries)
        kept = rng.sample(keys, round(fraction * len(keys)))
        return Plot({k: self._entries[k] for k in kept}, self.entry_bits)
