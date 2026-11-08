"""Forward Feistel permutation and a trusted inverse helper for tests."""

from __future__ import annotations

import hashlib


class FeistelPermutation:
    """Balanced Feistel permutation over an even-width domain."""

    is_permutation = True

    def __init__(self, master_key: bytes, n_bits: int, rounds: int = 8) -> None:
        if not isinstance(master_key, bytes) or len(master_key) != 16:
            raise ValueError("master_key must be exactly 16 bytes")
        if type(n_bits) is not int or n_bits < 2 or n_bits % 2:
            raise ValueError("n_bits must be an even integer of at least 2")
        if type(rounds) is not int or rounds < 1:
            raise ValueError("rounds must be a positive integer")

        self.N = 1 << n_bits
        self.output_bits = n_bits
        self.calls = 0
        self._half_bits = n_bits // 2
        self._half_bytes = (self._half_bits + 7) // 8
        self._mask = (1 << self._half_bits) - 1
        self._round_keys = tuple(
            hashlib.blake2b(
                b"feistel-round" + i.to_bytes(4, "big"),
                key=master_key,
                digest_size=32,
            ).digest()
            for i in range(rounds)
        )

    def __call__(self, x: int) -> int:
        if type(x) is not int or not 0 <= x < self.N:
            raise ValueError(f"input {x} outside domain [0, {self.N})")
        self.calls += 1
        left, right = x >> self._half_bits, x & self._mask
        for key in self._round_keys:
            left, right = right, left ^ self._round(right, key)
        return (left << self._half_bits) | right

    def _round(self, value: int, key: bytes) -> int:
        encoded = value.to_bytes(self._half_bytes, "big")
        digest = hashlib.blake2b(encoded, key=key, digest_size=32).digest()
        return int.from_bytes(digest, "big") >> (256 - self._half_bits)

    def reset_calls(self) -> None:
        self.calls = 0


def trusted_inverse(y: int, master_key: bytes, n_bits: int, rounds: int = 8) -> int:
    """Inverse for trusted tests/setup; not part of the forward oracle."""
    function = FeistelPermutation(master_key, n_bits, rounds)
    if type(y) is not int or not 0 <= y < function.N:
        raise ValueError(f"input {y} outside domain [0, {function.N})")
    left, right = y >> function._half_bits, y & function._mask
    for key in reversed(function._round_keys):
        left, right = right ^ function._round(left, key), left
    return (left << function._half_bits) | right
