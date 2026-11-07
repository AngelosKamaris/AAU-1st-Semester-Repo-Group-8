"""Tests for the time/storage attack. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import unittest

from pos import PoSParams, Verifier
from pos.schemes import SimpleScheme
from pos.provers import HonestProver, TimeStorageProver


def run(prover, scheme, challenges=200):
    """Returns (pass rate, average hash calls per challenge after setup)."""
    prover.setup()
    setup_calls = prover.queries
    verifier = Verifier(scheme, rng_seed=1)
    passed = 0
    for _ in range(challenges):
        y = verifier.new_challenge()
        passed += verifier.check(y, prover.answer(y))
    return passed / challenges, (prover.queries - setup_calls) / challenges


class TestTimeStorage(unittest.TestCase):
    """Test the relationship between storage usage and computation time."""
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=10, seed=7))
        self.N = self.scheme.params.N

    def test_always_answers_correctly(self):
        """Verify that the time-storage prover always produces valid answers."""
        for fraction in (0.0, 0.25, 0.5, 0.9):
            prover = TimeStorageProver(self.scheme, fraction, rng_seed=1)
            rate, _ = run(prover, self.scheme)
            self.assertEqual(rate, 1.0, f"fraction {fraction}")

    def test_stores_less_than_honest(self):
        """Verify that the time-storage prover uses less storage than 
        an honest prover when storing only 50% of the information."""
        honest = HonestProver(self.scheme)
        honest.setup()
        cheater = TimeStorageProver(self.scheme, 0.5, rng_seed=1)
        cheater.setup()
        self.assertAlmostEqual(cheater.storage_bits() / honest.storage_bits(), 0.5, delta=0.01)

    def test_storing_everything_needs_no_extra_work(self):
        """Verify that storing 100% of the information eliminates
        additional computation when answering challenges."""
        prover = TimeStorageProver(self.scheme, 1.0, rng_seed=1)
        _, calls = run(prover, self.scheme)
        self.assertEqual(calls, 0)

    def test_storing_nothing_is_brute_force(self):
        """Verify that storing 0% of the information requires brute-force
        computation (about N/2 hash calls per challenge)."""
        prover = TimeStorageProver(self.scheme, 0.0, rng_seed=1)
        _, calls = run(prover, self.scheme)
        self.assertAlmostEqual(calls / self.N, 0.5, delta=0.1)     # about N / 2

    def test_less_storage_means_more_time(self):
        """Verify that storing less information requires more computation
        when answering challenges."""
        calls = []
        for fraction in (0.9, 0.5, 0.1):
            prover = TimeStorageProver(self.scheme, fraction, rng_seed=1)
            calls.append(run(prover, self.scheme)[1])
        self.assertLess(calls[0], calls[1])
        self.assertLess(calls[1], calls[2])


if __name__ == "__main__":
    unittest.main()