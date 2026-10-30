"""Proof-of-space constructions. Add new ones here and register them in SCHEMES."""

from pos.schemes.base import Scheme
from pos.schemes.simple import SimpleScheme

# Name -> class, so experiments and the CLI can pick a scheme by name.
SCHEMES = {
    SimpleScheme.name: SimpleScheme,
}

__all__ = ["SCHEMES", "Scheme", "SimpleScheme"]
