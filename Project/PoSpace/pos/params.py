"""Shared parameters for a proof-of-space instance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

MAX_N_BITS = 24 # The table has N = 2**n_bits entries
SEED_BITS = 128 # HashFunction stores the seed in a 16-byte key.

@dataclass(frozen=True)
class PoSParams:
    """Settings that define one plot.

    n_bits: size of the domain. The function maps [0, N) -> [0, N), with N = 2**n_bits.
    seed:   BLAKE2b function seed or attack subset seed; not the verifier challenge seed.
    function: "feistel" or the original "blake2b".
    rounds: Feistel round count.
    master_key: optional 16-byte key for reproducible Feistel plots.
    """

    n_bits: int = 16
    seed: int = 1
    function: str = "feistel"
    rounds: int = 8
    master_key: Optional[bytes] = None

    def __post_init__(self) -> None:
        # type(...) is int also rejects bool (True would count as 1).
        if type(self.n_bits) is not int or not 1 <= self.n_bits <= MAX_N_BITS:
            raise ValueError(f"n_bits must be an integer between 1 and {MAX_N_BITS}")
        if type(self.seed) is not int or not 0 <= self.seed < 1 << SEED_BITS:
            raise ValueError(f"seed must be an integer between 0 and 2**{SEED_BITS} - 1")
        if self.function not in ("feistel", "blake2b"):
            raise ValueError("function must be 'feistel' or 'blake2b'")
        if self.function == "feistel" and (self.n_bits < 2 or self.n_bits % 2):
            raise ValueError("Feistel requires an even n_bits value of at least 2")
        if type(self.rounds) is not int or self.rounds < 1:
            raise ValueError("rounds must be a positive integer")
        if self.master_key is not None and (
            not isinstance(self.master_key, bytes) or len(self.master_key) != 16
        ):
            raise ValueError("master_key must be exactly 16 bytes")

    @property
    def N(self) -> int:
        """Domain size."""
        return 1 << self.n_bits
