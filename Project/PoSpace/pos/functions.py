"""The functions a prover has to invert.

Every function counts how many times it is evaluated (`calls`). That count is
the "T" (time) in the paper's S/T trade-offs, so experiments can report work
in a way that doesn't depend on how fast someone's laptop is.
"""

from __future__ import annotations

import hashlib


class HashFunction:
    """f(x) = BLAKE2b(seed, x), using the full 256-bit hash output.

    Inputs x come from [0, N), with N = 2**n_bits. Outputs are the full hash,
    not reduced mod N, so the hash keeps its full strength. With so many
    possible outputs, two different x practically never give the same y.

    Note: finding x for a given y still takes at most N tries (there are only
    N possible inputs). That is what the proof of space relies on.
    """

    OUTPUT_BYTES = 32                  # full BLAKE2b-256 output
    output_bits = OUTPUT_BYTES * 8     # 256

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
            x.to_bytes(self._x_bytes, "big"), key=self._key, digest_size=self.OUTPUT_BYTES
        ).digest()
        return int.from_bytes(digest, "big")

    def reset_calls(self) -> None:
        self.calls = 0
