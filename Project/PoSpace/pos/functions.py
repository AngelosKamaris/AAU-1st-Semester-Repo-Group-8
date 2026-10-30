"""The functions a prover has to invert.

Every function counts how many times it is evaluated (`calls`). That count is
the "T" (time) in the paper's S/T trade-offs, so experiments can report work
in a way that doesn't depend on how fast someone's laptop is.
"""

from __future__ import annotations

import hashlib


class HashFunction:
    """f(x) = H(seed, x) mod N, built from BLAKE2b.

    Behaves like a random function: outputs look random, some outputs repeat
    (collisions) and some outputs are never produced. This is the
    "rand(x, seed) mod N" box in the design diagram.
    """

    def __init__(self, seed: int, n_bits: int, domain_tag: bytes = b"f") -> None:
        self.seed = seed
        self.n_bits = n_bits
        self.N = 1 << n_bits
        # The key makes this a different function for every seed (and tag).
        # The tag lets later constructions derive several independent
        # functions (e.g. f and g) from the same seed.
        self._key = domain_tag + seed.to_bytes(16, "big")
        self._x_bytes = max(1, (n_bits + 7) // 8)
        self.calls = 0

    def __call__(self, x: int) -> int:
        if not 0 <= x < self.N:
            raise ValueError(f"input {x} outside domain [0, {self.N})")
        self.calls += 1
        digest = hashlib.blake2b(
            x.to_bytes(self._x_bytes, "big"), key=self._key, digest_size=8
        ).digest()
        return int.from_bytes(digest, "big") & (self.N - 1)

    def reset_calls(self) -> None:
        self.calls = 0
