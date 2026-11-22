"""Basic correctness tests. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import hashlib
import unittest

from pos import PoSParams, Verifier
from pos.functions import HashFunction
from pos.provers import HonestProver
from pos.schemes import SimpleScheme


class TestHashFunction(unittest.TestCase):
    def test_deterministic_and_in_domain(self):
        first, second = HashFunction(3, 9), HashFunction(3, 9)
        for value in range(first.N):
            output = first(value)
            self.assertEqual(output, second(value))
            self.assertTrue(0 <= output < first.N)

    def test_retains_first_bits_of_full_digest(self):
        digest = hashlib.blake2b(b"\x00\x01", key=b"f" + (3).to_bytes(16, "big")).digest()
        self.assertEqual(HashFunction(3, 9)(1), int.from_bytes(digest[:2], "big") >> 7)

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

    def test_plot_processes_all_inputs_and_keeps_each_distinct_output(self):
        prover = HonestProver(self.scheme)
        prover.setup()
        self.assertEqual(prover.queries, self.scheme.params.N)
        outputs = {self.verifier.f(value) for value in range(self.scheme.params.N)}
        self.assertEqual(len(prover.plot), len(outputs))
        for output in outputs:
            self.assertTrue(self.verifier.check(output, prover.answer(output)))


if __name__ == "__main__":
    unittest.main()
