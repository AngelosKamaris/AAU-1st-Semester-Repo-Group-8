"""The table a prover stores (the "plot")."""

from __future__ import annotations

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
