"""Tests for the partial storage attack. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import unittest

from pos import PoSParams, Verifier
from pos.provers import HonestProver, PartialStorageProver
from pos.schemes import SimpleScheme


def pass_rate(prover, scheme, challenges=300):
    prover.setup()
    verifier = Verifier(scheme, rng_seed=1)
    passed = 0
    for _ in range(challenges):
        y = verifier.new_challenge()
        passed += verifier.check(y, prover.answer(y))
    return passed / challenges


class TestPartialStorage(unittest.TestCase):
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=10, seed=7))
        self.N = self.scheme.params.N

    def test_keeps_the_right_share_of_the_table(self):
        honest = HonestProver(self.scheme)
        honest.setup()
        cheater = PartialStorageProver(self.scheme, fraction=0.5, rng_seed=1)
        cheater.setup()
        self.assertAlmostEqual(len(cheater.plot) / len(honest.plot), 0.5, delta=0.01)

    def test_storing_nothing_fails(self):
        cheater = PartialStorageProver(self.scheme, fraction=0.0, rng_seed=1)
        self.assertEqual(pass_rate(cheater, self.scheme), 0.0)

    def test_storing_everything_passes(self):
        cheater = PartialStorageProver(self.scheme, fraction=1.0, rng_seed=1)
        self.assertEqual(pass_rate(cheater, self.scheme), 1.0)

    def test_half_storage_passes_about_half(self):
        cheater = PartialStorageProver(self.scheme, fraction=0.5, rng_seed=1)
        self.assertAlmostEqual(pass_rate(cheater, self.scheme), 0.5, delta=0.12)

    def test_never_does_extra_work(self):
        cheater = PartialStorageProver(self.scheme, fraction=0.5, rng_seed=1)
        pass_rate(cheater, self.scheme)
        self.assertEqual(cheater.queries, self.N)  # only the setup hashes, nothing per challenge


if __name__ == "__main__":
    unittest.main()
