""" 
Attack 2: simple time/storage trade-off.

Following the partial storage attack, the cheater keeps only a `fraction` of the table. The difference is what it 
does on a miss. Instead of giving up, it brute-forces: it evaluates f on inputs x it did not store until f(x) = y.

  - answer in the stored part  -> instant lookup, 0 hash calls;
  - answer in the dropped part -> search the dropped inputs, which costs up to (1-p) * N hash calls.

This means the cheater can always produce a correct answer while using less storage than an honest prover, 
at the cost of additional computation.
With distinct outputs, a cheater keeping a fraction p does about (1-p)^2 * N/2
calls per challenge, with worst-case work N - S for S stored entries. Collisions
can allow an earlier match, so N - S is only an upper bound in general.
"""

from __future__ import annotations

from itertools import islice
from typing import Any, Optional

from pos.schemes.base import Scheme
from pos.provers.partial_storage import PartialStorageProver


class TimeStorageProver(PartialStorageProver):
    """Prover implementing a time/storage trade-off attack."""
    def __init__(self, scheme: Scheme, fraction: float, rng_seed: Optional[int] = None,
                 online_query_budget: Optional[int] = None) -> None:
        super().__init__(scheme, fraction, rng_seed)
        if online_query_budget is not None and (type(online_query_budget) is not int or online_query_budget < 0):
            raise ValueError("online_query_budget must be a non-negative integer")
        self.online_query_budget = online_query_budget
        self.name = f"time-storage({fraction:.0%} stored)"

    def setup(self) -> None:
        """Build the plot and remember which inputs are stored."""
        super().setup()
        # Save inputs x that are stored (from PartialStorageProver).
        # For each we know f(x), so brute force can skip them.
        self._stored_inputs = set(self.plot._entries.values())

    def answer(self, y: int) -> Optional[Any]:
        """Answer a verifier challenge using lookup or brute-force search."""
        x = self.plot.lookup(y)
        if x is not None: return x                    # in the stored part: lookup
        domain_size = self.scheme.params.N
        budget = self.online_query_budget
        inputs = (value for value in range(domain_size) if value not in self._stored_inputs)
        for value in islice(inputs, min(budget, domain_size) if budget is not None else None):
            if self.f(value) == y:
                return value
        return None


class PairedTimeStorageProver(TimeStorageProver):
    """Keep only the retained plot entries; rebuild public pair candidates on a miss."""

    def setup(self) -> None:
        PartialStorageProver.setup(self)

    def answer(self, y: int) -> Optional[tuple[int, int]]:
        pair = self.plot.lookup(y)
        if pair is not None:
            return pair
        return self.scheme.recover(self.f, y, self.online_query_budget)
