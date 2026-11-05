"""What every proof-of-space construction must provide.

A "scheme" bundles the parts that change from one construction to the next:
  - which function is used,
  - how the plot (table) is built from it,
  - how the verifier picks a challenge,
  - how the verifier checks an answer.

The prover and verifier only talk to this interface, so a new construction
later on (e.g. the collision-based g_f) is one new scheme file.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any

from pos.params import PoSParams
from pos.plot import Plot


class Scheme(ABC):
    name: str = "scheme"

    def __init__(self, params: PoSParams) -> None:
        self.params = params

    @abstractmethod
    def new_function(self) -> Any:
        """A fresh function for one party (each party counts its own calls)."""

    @abstractmethod
    def build_plot(self, function: Any) -> Plot:
        """Initialization: compute and return the full table."""

    @abstractmethod
    def sample_challenge(self, function: Any, rng: random.Random) -> int:
        """Verifier side: pick a challenge y."""

    @abstractmethod
    def is_valid(self, function: Any, y: int, answer: Any) -> bool:
        """Verifier side: check that `answer` really solves challenge y."""
