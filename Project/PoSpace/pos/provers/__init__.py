"""Provers. Later attacks go here as Prover subclasses."""

from pos.provers.base import Prover
from pos.provers.honest import HonestProver

__all__ = ["HonestProver", "Prover"]
