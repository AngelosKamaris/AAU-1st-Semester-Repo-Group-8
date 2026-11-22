"""Shared parameters for a proof-of-space instance."""

from __future__ import annotations

from dataclasses import dataclass

MAX_N_BITS = 24 # The table has N = 2**n_bits entries
SEED_BITS = 128 # HashFunction stores the seed in a 16-byte key.

@dataclass(frozen=True)
class PoSParams:
    """Settings that define one plot.

    n_bits: size of the domain. The function maps [0, N) -> [0, N), with N = 2**n_bits.
    seed:   public seed for f and the attack subset; not the verifier challenge seed.
    seed_g: public seed for the Stage 3 pair hash.
    """

    n_bits: int = 16
    seed: int = 1
    seed_g: int = 2

    def __post_init__(self) -> None:
        # type(...) is int also rejects bool (True would count as 1).
        if type(self.n_bits) is not int or not 1 <= self.n_bits <= MAX_N_BITS:
            raise ValueError(f"n_bits must be an integer between 1 and {MAX_N_BITS}")
        for name, seed in (("seed", self.seed), ("seed_g", self.seed_g)):
            if type(seed) is not int or not 0 <= seed < 1 << SEED_BITS:
                raise ValueError(f"{name} must be an integer between 0 and 2**{SEED_BITS} - 1")

    @property
    def N(self) -> int:
        """Domain size."""
        return 1 << self.n_bits
