"""Basic correctness tests. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import unittest

from pos import PoSParams, Verifier
from pos.feistel import FeistelPermutation, trusted_inverse
from pos.functions import HashFunction
from pos.provers import HonestProver
from pos.schemes import SimpleScheme


class TestFeistelPermutation(unittest.TestCase):
    def test_16_bit_mapping_is_a_permutation_and_inverse_recovers_input(self):
        key = bytes.fromhex("00112233445566778899aabbccddeeff")
        function = FeistelPermutation(key, 16)
        outputs = [function(x) for x in range(function.N)]
        self.assertEqual(len(set(outputs)), function.N)
        self.assertTrue(all(0 <= y < function.N for y in outputs))
        for x, y in enumerate(outputs):
            self.assertEqual(trusted_inverse(y, key, 16), x)

    def test_same_key_is_deterministic_and_another_key_changes_mapping(self):
        key = bytes(16)
        first = FeistelPermutation(key, 8)
        second = FeistelPermutation(key, 8)
        other = FeistelPermutation(bytes([1]) + bytes(15), 8)
        self.assertEqual([first(x) for x in range(first.N)], [second(x) for x in range(second.N)])
        self.assertNotEqual([first(x) for x in range(first.N)], [other(x) for x in range(other.N)])

    def test_forward_function_does_not_expose_inverse_or_plot(self):
        function = FeistelPermutation(bytes(16), 8)
        self.assertFalse(hasattr(function, "inverse"))
        self.assertFalse(hasattr(function, "table"))


class TestHashFunction(unittest.TestCase):
    def test_deterministic_and_full_size(self):
        f, g = HashFunction(3, 8), HashFunction(3, 8)
        for x in range(256):
            self.assertEqual(f(x), g(x))
            self.assertTrue(0 <= f(x) < 2 ** HashFunction.output_bits)

    def test_no_collisions_with_full_output(self):
        f = HashFunction(3, 10)
        outputs = [f(x) for x in range(1024)]
        self.assertEqual(len(set(outputs)), 1024)

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
