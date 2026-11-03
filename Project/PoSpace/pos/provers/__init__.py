"""Provers. Every attack is a Prover subclass."""

from pos.provers.base import Prover
from pos.provers.honest import HonestProver
from pos.provers.partial_storage import PartialStorageProver

__all__ = ["HonestProver", "PartialStorageProver", "Prover"]
