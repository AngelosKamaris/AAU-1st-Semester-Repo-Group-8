"""Basic correctness tests. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import unittest

from pos import PoSParams, Verifier
from pos.functions import HashFunction
from pos.provers import HonestProver
from pos.schemes import SimpleScheme


class TestHashFunction(unittest.TestCase):
    def test_deterministic_and_in_range(self):
        f, g = HashFunction(3, 8), HashFunction(3, 8)
        for x in range(256):
            self.assertEqual(f(x), g(x))
            self.assertTrue(0 <= f(x) < 256)

    def test_different_seeds_give_different_functions(self):
        f, g = HashFunction(1, 12), HashFunction(2, 12)
        self.assertNotEqual([f(x) for x in range(50)], [g(x) for x in range(50)])


class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=10, seed=7))
        self.verifier = Verifier(self.scheme, rng_seed=1)

    def test_honest_prover_always_passes(self):
        prover = HonestProver(self.scheme)
        prover.setup()
        for _ in range(200):
            y = self.verifier.new_challenge()
            self.assertTrue(self.verifier.check(y, prover.answer(y)))

    def test_verifier_rejects_wrong_answers(self):
        y = self.verifier.new_challenge()
        wrong = next(x for x in range(self.scheme.params.N) if self.verifier.f(x) != y)
        self.assertFalse(self.verifier.check(y, wrong))
        self.assertFalse(self.verifier.check(y, None))
        self.assertFalse(self.verifier.check(y, -1))


if __name__ == "__main__":
    unittest.main()
