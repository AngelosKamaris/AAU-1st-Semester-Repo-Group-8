"""The simple proof of space (no security measures yet).

Initialization: the prover computes f(x) for every x and stores y -> x.
Challenge:      the verifier picks a random x and sends y = f(x).
Answer:         the prover looks up y and returns an x' with f(x') = y.
Check:          the verifier computes f(x') and compares it with y.
"""

from __future__ import annotations

import random
import secrets
from typing import Any

from pos.feistel import FeistelPermutation
from pos.functions import HashFunction
from pos.params import PoSParams
from pos.plot import Plot
from pos.schemes.base import Scheme


class SimpleScheme(Scheme):
    name = "simple"

    def __init__(self, params: PoSParams) -> None:
        super().__init__(params)
        self._master_key = params.master_key or secrets.token_bytes(16)

    def new_function(self) -> Any:
        if self.params.function == "feistel":
            return FeistelPermutation(
                self._master_key, self.params.n_bits, self.params.rounds
            )
        return HashFunction(self.params.seed, self.params.n_bits)

    def build_plot(self, function: Any) -> Plot:
        table = {}
        for x in range(self.params.N):
            table.setdefault(function(x), x)
        if getattr(function, "is_permutation", False) and len(table) != self.params.N:
            raise RuntimeError("Feistel function did not produce a permutation")
        entry_bits = function.output_bits + self.params.n_bits
        return Plot(table, entry_bits=entry_bits)

    def sample_challenge(self, function: Any, rng: random.Random) -> int:
        if getattr(function, "is_permutation", False):
            return rng.randrange(self.params.N)
        # Picking y = f(x) for a random x guarantees an answer exists.
        return function(rng.randrange(self.params.N))

    def is_valid(self, function: Any, y: int, answer: Any) -> bool:
        # The answer comes from the prover: only evaluate f on a real int in [0, N).
        if not self.is_domain_element(answer):
            return False
        return function(answer) == y
