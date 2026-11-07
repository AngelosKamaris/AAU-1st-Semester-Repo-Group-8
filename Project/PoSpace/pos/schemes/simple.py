"""The simple proof of space (no security measures yet).

Initialization: the prover computes f(x) for every x and stores y -> x.
Challenge:      the verifier picks a random x and sends y = f(x).
Answer:         the prover looks up y and returns an x' with f(x') = y.
Check:          the verifier computes f(x') and compares it with y.
"""

from __future__ import annotations

import random
from typing import Any

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
            # With the full hash output, two x practically never share a y.
            # If they ever did, either x is a valid answer, so keep the first.
            table.setdefault(function(x), x)
        # One entry stores the y (full hash output) and its x (n_bits).
        entry_bits = function.output_bits + self.params.n_bits
        return Plot(table, entry_bits=entry_bits)

    def sample_challenge(self, function: HashFunction, rng: random.Random) -> int:
        # Picking y = f(x) for a random x guarantees an answer exists.
        return function(rng.randrange(self.params.N))

    def is_valid(self, function: HashFunction, y: int, answer: Any) -> bool:
        # The answer comes from the prover: only evaluate f on a real int in [0, N).
        if not self.is_domain_element(answer):
            return False
        return function(answer) == y
