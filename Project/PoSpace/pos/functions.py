"""The functions a prover has to invert.

Every function counts how many times it is evaluated (`calls`). That count is
the "T" (time) in the paper's S/T trade-offs, so experiments can report work
in a way that doesn't depend on how fast someone's laptop is.
"""

from __future__ import annotations

import hashlib


class HashFunction:
    """A seeded BLAKE2b function truncated to the first n_bits of its digest."""

    def __init__(self, seed: int, n_bits: int, domain_tag: bytes = b"f", arity: int = 1) -> None:
        self.seed = seed
        self.n_bits = n_bits
        self.N = 1 << n_bits
        self._arity = arity
        # The key makes this a different function for every seed (and tag).
        # The tag lets later constructions derive several independent
        # functions (e.g. f and g) from the same seed.
        self._key = domain_tag + seed.to_bytes(16, "big")
        self._x_bytes = max(1, (n_bits + 7) // 8)
        self.calls = 0

    def __call__(self, x: int, *partners: int) -> int:
        if 1 + len(partners) != self._arity:
            raise TypeError(f"expected {self._arity} inputs")
        encoded = bytearray()
        for value in (x, *partners):
            if not 0 <= value < self.N:
                raise ValueError(f"input {value} outside domain [0, {self.N})")
            encoded.extend(value.to_bytes(self._x_bytes, "big"))
        self.calls += 1
        digest = hashlib.blake2b(encoded, key=self._key).digest()
        return int.from_bytes(digest, "big") >> (len(digest) * 8 - self.n_bits)

    def reset_calls(self) -> None:
        self.calls = 0


def pi(output: int, n_bits: int) -> int:
    return output ^ ((1 << n_bits) - 1)
