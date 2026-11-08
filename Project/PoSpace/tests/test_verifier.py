"""The verifier must reject malformed answers without crashing. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import argparse
import subprocess
import sys
import unittest

from pos import PoSParams, Verifier
from pos.cli import challenges_arg, fraction, n_bits_arg, seed_arg
from pos.params import MAX_N_BITS
from pos.provers import PartialStorageProver, TimeStorageProver
from pos.schemes import SimpleScheme


class TestAnswerSanitizing(unittest.TestCase):
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=8, seed=3))
        self.verifier = Verifier(self.scheme, rng_seed=1)
        self.N = self.scheme.params.N

    def challenge_for(self, x):
        return self.verifier.f(x)

    def test_valid_int_is_accepted(self):
        self.assertTrue(self.verifier.check(self.challenge_for(68), 68))

    def test_wrong_int_is_rejected(self):
        self.assertFalse(self.verifier.check(self.challenge_for(68), 69))

    def test_non_integers_are_rejected_not_crashing(self):
        y = self.challenge_for(68)
        for bad in (68.0, "68", b"68", [68], (68,), {68}, 68 + 0j, None, object()):
            with self.subTest(answer=bad):
                self.assertFalse(self.verifier.check(y, bad))

    def test_bool_is_not_an_integer_answer(self):
        self.assertFalse(self.verifier.check(self.challenge_for(1), True))
        self.assertFalse(self.verifier.check(self.challenge_for(0), False))

    def test_out_of_range_is_rejected(self):
        y = self.challenge_for(68)
        for bad in (-1, self.N, 10 ** 100):
            with self.subTest(answer=bad):
                self.assertFalse(self.verifier.check(y, bad))

    def test_rejected_answers_cost_the_verifier_no_hash_calls(self):
        before = self.verifier.f.calls
        self.verifier.check(self.challenge_for(5), "5")
        self.assertEqual(self.verifier.f.calls - before, 1)   # only the challenge_for call


class TestParamsValidation(unittest.TestCase):
    def test_valid_params(self):
        self.assertEqual(PoSParams(n_bits=1, seed=0, function="blake2b").N, 2)
        self.assertEqual(PoSParams(n_bits=MAX_N_BITS, seed=2 ** 128 - 1).n_bits, MAX_N_BITS)

    def test_feistel_requires_even_n_bits(self):
        for n_bits in (1, 3, 5):
            with self.subTest(n_bits=n_bits), self.assertRaises(ValueError):
                PoSParams(n_bits=n_bits)

    def test_bad_n_bits(self):
        for bad in (0, -1, MAX_N_BITS + 1, 40, True, 2.5, "8", None):
            with self.subTest(n_bits=bad), self.assertRaises(ValueError):
                PoSParams(n_bits=bad)

    def test_bad_seed(self):
        for bad in (-1, 2 ** 128, True, 2.5, "1", None):
            with self.subTest(seed=bad), self.assertRaises(ValueError):
                PoSParams(seed=bad)


class TestProverSettingsValidation(unittest.TestCase):
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=6))

    def test_bad_fraction(self):
        for cls in (PartialStorageProver, TimeStorageProver):
            for bad in (-0.1, 1.1, 2, float("nan"), float("inf"), True, "0.5", None):
                with self.subTest(prover=cls.__name__, fraction=bad), self.assertRaises(ValueError):
                    cls(self.scheme, bad)

    def test_good_fraction(self):
        for good in (0, 0.0, 0.25, 1, 1.0):
            PartialStorageProver(self.scheme, good)
            TimeStorageProver(self.scheme, good)


class TestCommandLineValidation(unittest.TestCase):
    def test_validators_accept_good_values(self):
        self.assertEqual(n_bits_arg("12"), 12)
        self.assertEqual(seed_arg("0"), 0)
        self.assertEqual(challenges_arg("5"), 5)
        self.assertEqual(fraction("0.25"), 0.25)

    def test_validators_reject_bad_values(self):
        cases = [(n_bits_arg, ["0", "-1", str(MAX_N_BITS + 1), "40", "2.5", "abc"]),
                 (seed_arg, ["-1", str(2 ** 128), "1.5", "x"]),
                 (challenges_arg, ["0", "-2", "1.5", "x"]),
                 (fraction, ["-0.1", "1.5", "nan", "inf", "abc"])]
        for validator, values in cases:
            for bad in values:
                with self.subTest(validator=validator.__name__, value=bad), \
                        self.assertRaises(argparse.ArgumentTypeError):
                    validator(bad)

    def test_main_gives_usage_error_not_traceback(self):
        for args in (["--challenges", "0"], ["--n-bits", "40"], ["--n-bits", "3"], ["--fraction", "2"]):
            with self.subTest(args=args):
                run = subprocess.run([sys.executable, "main.py", *args], capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertIn("error:", run.stderr)
                self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()