""" 
Attack 2: simple time/storage trade-off.

Following the partial storage attack, the cheater keeps only a `fraction` of the table. The difference is what it 
does on a miss. Instead of giving up, it brute-forces: it evaluates f on inputs x it did not store until f(x) = y.

  - answer in the stored part  -> instant lookup, 0 hash calls;
  - answer in the dropped part -> search the dropped inputs, which costs up to (1-p) * N hash calls.

This means the cheater can always produce a correct answer while using less storage than an honest prover, 
at the cost of additional computation.
A cheater keeping a fraction p of the table does on average (1-p)^2 * N/2 hash calls per challenge: space and 
time trade off linearly (S*T is about N), instead of the all-or-nothing behaviour of the honest prover.
"""

from __future__ import annotations

from typing import Optional

from pos.schemes.base import Scheme
from pos.provers.partial_storage import PartialStorageProver


class TimeStorageProver(PartialStorageProver):
    """Prover implementing a time/storage trade-off attack."""
    def __init__(self, scheme: Scheme, fraction: float, rng_seed: Optional[int] = None) -> None:
        super().__init__(scheme, fraction, rng_seed)
        self.name = f"time-storage({fraction:.0%} stored)"

    def setup(self) -> None:
        """Build the plot and remember which inputs are stored."""
        super().setup()
        # Save inputs x that are stored (from PartialStorageProver).
        # For each we know f(x), so brute force can skip them.
        self._stored_inputs = set(self.plot._entries.values())

    def answer(self, y: int) -> Optional[int]:
        """Answer a verifier challenge using lookup or brute-force search."""
        x = self.plot.lookup(y)
        if x is not None: return x                    # in the stored part: lookup
        for x in range(self.scheme.params.N):         # otherwise: brute force
            if x not in self._stored_inputs and self.f(x) == y:
                return x
        return None