"""Shared parameters for a proof-of-space instance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PoSParams:
    """Settings that define one plot.

    n_bits: size of the domain. The function maps [0, N) -> [0, N), with N = 2**n_bits.
    seed:   unique number of the plot. Different seeds give unrelated functions,
            so a table built for one seed is useless for another.
    """

    n_bits: int = 8
    seed: int = 1

    def __post_init__(self) -> None:
        if self.n_bits < 1:
            raise ValueError("n_bits must be at least 1")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")

    @property
    def N(self) -> int:
        """Domain size."""
        return 1 << self.n_bits
