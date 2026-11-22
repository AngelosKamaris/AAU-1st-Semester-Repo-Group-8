"""Stage 3: index ordered inputs whose f-outputs are complements."""

from __future__ import annotations

import random
from typing import Any, Iterator, Optional

from pos.functions import HashFunction, pi
from pos.params import PoSParams
from pos.plot import Plot
from pos.schemes.base import Scheme


class PairFunctions:
    def __init__(self, params: PoSParams) -> None:
        self.f = HashFunction(params.seed, params.n_bits)
        self.g = HashFunction(params.seed_g, params.n_bits, b"g", arity=2)

    @property
    def calls(self) -> int:
        return self.f.calls + self.g.calls


class PairedPlot(Plot):
    def __init__(self, table: dict[int, tuple[int, int]], n_bits: int,
                 pair_count: int, unpaired: int) -> None:
        super().__init__(table, entry_bits=3 * n_bits)
        self.pair_count = pair_count
        self.unpaired = unpaired


class PairedScheme(Scheme):
    name = "paired"

    def new_function(self) -> PairFunctions:
        return PairFunctions(self.params)

    def _pairs(self, function: PairFunctions, groups: dict[int, list[int]],
               stop_at: Optional[int] = None) -> Iterator[tuple[int, int]]:
        """Add inputs to output buckets and emit both orders when a match first appears."""
        for value in range(self.params.N):
            if stop_at is not None and function.calls >= stop_at:
                return
            output = function.f(value)
            for partner in groups.get(pi(output, self.params.n_bits), ()):
                yield value, partner
                yield partner, value
            groups.setdefault(output, []).append(value)

    def build_plot(self, function: PairFunctions) -> PairedPlot:
        groups = {}
        table = {}
        calls_before = function.g.calls
        for pair in self._pairs(function, groups):
            table.setdefault(function.g(*pair), pair)
        unpaired = sum(len(group) for output, group in groups.items()
                       if pi(output, self.params.n_bits) not in groups)
        return PairedPlot(table, self.params.n_bits, function.g.calls - calls_before, unpaired)

    def sample_challenge(self, function: PairFunctions, rng: random.Random) -> int:
        return rng.randrange(self.params.N)

    def is_valid(self, function: PairFunctions, y: int, answer: Any) -> bool:
        if type(answer) is not tuple or len(answer) != 2:
            return False
        first, second = answer
        if not self.is_domain_element(first) or not self.is_domain_element(second):
            return False
        return (function.f(second) == pi(function.f(first), self.params.n_bits)
                and function.g(first, second) == y)

    def recover(self, function: PairFunctions, y: int, budget: Optional[int]) -> Optional[tuple[int, int]]:
        stop_at = None if budget is None else function.calls + budget
        for pair in self._pairs(function, {}, stop_at):
            if stop_at is not None and function.calls >= stop_at:
                break
            if function.g(*pair) == y:
                return pair
        return None
