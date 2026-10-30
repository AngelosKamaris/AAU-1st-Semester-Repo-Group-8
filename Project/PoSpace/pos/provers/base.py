"""The prover interface.

Later attacks will be subclasses of Prover with a different `setup` (what
they keep) and `answer` (how they respond).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pos.schemes.base import Scheme


class Prover(ABC):
    name: str = "prover"

    def __init__(self, scheme: Scheme) -> None:
        self.scheme = scheme
        # The prover's own copy of the function. Its call counter measures
        # how much work the prover does.
        self.f = scheme.new_function()

    @abstractmethod
    def setup(self) -> None:
        """Initialization phase: build whatever the prover will store."""

    @abstractmethod
    def answer(self, y: int) -> Optional[Any]:
        """Respond to challenge y, or return None if no answer is found."""

    @abstractmethod
    def storage_bits(self) -> int:
        """How much the prover keeps after setup."""

    @property
    def queries(self) -> int:
        """Total function evaluations so far."""
        return self.f.calls
