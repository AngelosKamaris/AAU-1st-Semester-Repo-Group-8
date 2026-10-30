"""The simple proof of space (no security measures yet).

Initialization: the prover computes f(x) for every x and stores y -> x.
Challenge:      the verifier picks a random x and sends y = f(x).
Answer:         the prover looks up y and returns an x' with f(x') = y.
Check:          the verifier computes f(x') and compares it with y.
"""

from __future__ import annotations

import random
from typing import Optional

from pos.functions import HashFunction
from pos.plot import Plot
from pos.schemes.base import Scheme


class SimpleScheme(Scheme):
    name = "simple"

    def new_function(self) -> HashFunction:
        return HashFunction(self.params.seed, self.params.n_bits)

    def build_plot(self, function: HashFunction) -> Plot:
        table = {}
        for x in range(self.params.N):
            # Several x can give the same y (collisions). Any one of them is a
            # valid answer, so we keep the first and skip the rest.
            table.setdefault(function(x), x)
        # One entry stores an x of n_bits. (y is the position in a sorted
        # table, so it doesn't need to be stored explicitly.)
        return Plot(table, entry_bits=self.params.n_bits)

    def sample_challenge(self, function: HashFunction, rng: random.Random) -> int:
        # Picking y = f(x) for a random x guarantees an answer exists.
        return function(rng.randrange(self.params.N))

    def is_valid(self, function: HashFunction, y: int, answer: Optional[int]) -> bool:
        if answer is None or not 0 <= answer < self.params.N:
            return False
        return function(answer) == y
