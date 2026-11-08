"""Validators for command-line arguments.

They give a clear usage error instead of a traceback, and stop values such as
--challenges 0 (division by zero) or --n-bits 40 (a table that cannot fit in memory).
"""

from __future__ import annotations

import argparse
from typing import Callable, Optional

from pos.params import MAX_N_BITS, SEED_BITS


def int_in_range(low: int, high: Optional[int] = None) -> Callable[[str], int]:
    """argparse type: an integer with low <= value (<= high)."""
    def parse(text: str) -> int:
        try: value = int(text)
        except ValueError: raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from None
        if value < low or (high is not None and value > high):
            where = f"between {low} and {high}" if high is not None else f"at least {low}"
            raise argparse.ArgumentTypeError(f"must be {where}, got {value}")
        return value
    return parse


def fraction(text: str) -> float:
    """argparse type: a number from 0 to 1 (nan and inf are rejected)."""
    try: value = float(text)
    except ValueError: raise argparse.ArgumentTypeError(f"{text!r} is not a number") from None
    if not 0.0 <= value <= 1.0: raise argparse.ArgumentTypeError(f"must be between 0 and 1, got {text}")
    return value


n_bits_arg = int_in_range(1, MAX_N_BITS)
seed_arg = int_in_range(0, (1 << SEED_BITS) - 1)
challenges_arg = int_in_range(1)
rounds_arg = int_in_range(1, 1000)


def master_key_arg(text: str) -> bytes:
    """Parse a 128-bit Feistel key written as hexadecimal."""
    try:
        key = bytes.fromhex(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a 32-character hexadecimal key") from None
    if len(key) != 16 or len(text) != 32:
        raise argparse.ArgumentTypeError("must be a 32-character hexadecimal key")
    return key