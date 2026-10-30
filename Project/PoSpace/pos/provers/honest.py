"""The honest prover: stores the whole plot and answers by lookup."""

from __future__ import annotations

from typing import Any, Optional

from pos.plot import Plot
from pos.provers.base import Prover


class HonestProver(Prover):
    name = "honest"

    def setup(self) -> None:
        self.plot: Plot = self.scheme.build_plot(self.f)

    def answer(self, y: int) -> Optional[Any]:
        return self.plot.lookup(y)

    def storage_bits(self) -> int:
        return self.plot.storage_bits()
