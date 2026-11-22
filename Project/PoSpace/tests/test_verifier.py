"""The verifier must reject malformed answers without crashing. Run with:  python -m unittest discover tests"""

from __future__ import annotations

import argparse
import io
import random
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from pos import PoSParams, Verifier
from pos.cli import challenges_arg, fraction, n_bits_arg, positive_milliseconds, seed_arg
from pos.params import MAX_N_BITS
from pos.provers import HonestProver, PartialStorageProver, TimeStorageProver
from pos.schemes import SimpleScheme
from pos.session import STAGE_2_CHALLENGES, run_trials


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


class TestResponseDeadline(unittest.TestCase):
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=8, seed=3))
        self.verifier = Verifier(
            self.scheme, rng_seed=1, max_response_time_ms=0.1
        )
        self.y = self.verifier.f(68)

    def test_valid_answer_passes_at_or_before_deadline(self):
        self.assertTrue(self.verifier.check(self.y, 68, response_time_ms=0.1))
        self.assertTrue(self.verifier.check(self.y, 68, response_time_ms=0.099))

    def test_late_answer_fails_without_hashing_it(self):
        before = self.verifier.f.calls
        self.assertFalse(self.verifier.check(self.y, 68, response_time_ms=0.1001))
        self.assertEqual(self.verifier.f.calls, before)

    def test_missing_or_invalid_elapsed_time_fails_closed(self):
        for elapsed in (None, -0.1, float("nan"), float("inf"), True):
            with self.subTest(elapsed=elapsed):
                self.assertFalse(
                    self.verifier.check(self.y, 68, response_time_ms=elapsed)
                )

    def test_deadline_must_be_finite_and_positive(self):
        for deadline in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(deadline=deadline), self.assertRaises(ValueError):
                Verifier(self.scheme, max_response_time_ms=deadline)


class TestChallengeRandomness(unittest.TestCase):
    def setUp(self):
        self.scheme = SimpleScheme(PoSParams(n_bits=8, seed=3))

    def test_unseeded_verifier_uses_system_randomness(self):
        self.assertIsInstance(Verifier(self.scheme).rng, random.SystemRandom)

    def test_explicit_seed_keeps_experiments_reproducible(self):
        first = Verifier(self.scheme, rng_seed=1)
        second = Verifier(self.scheme, rng_seed=1)
        self.assertEqual(
            [first.new_challenge() for _ in range(10)],
            [second.new_challenge() for _ in range(10)],
        )


class TestParamsValidation(unittest.TestCase):
    def test_valid_params(self):
        self.assertEqual(PoSParams(n_bits=1, seed=0).N, 2)
        self.assertEqual(PoSParams(n_bits=MAX_N_BITS, seed=2 ** 128 - 1).n_bits, MAX_N_BITS)

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
        self.assertEqual(positive_milliseconds("0.001"), 0.001)

    def test_validators_reject_bad_values(self):
        cases = [(n_bits_arg, ["0", "-1", str(MAX_N_BITS + 1), "40", "2.5", "abc"]),
                 (seed_arg, ["-1", str(2 ** 128), "1.5", "x"]),
                 (challenges_arg, ["0", "-2", "1.5", "x"]),
                 (fraction, ["-0.1", "1.5", "nan", "inf", "abc"]),
                 (positive_milliseconds, ["0", "-0.1", "nan", "inf", "abc"])]
        for validator, values in cases:
            for bad in values:
                with self.subTest(validator=validator.__name__, value=bad), \
                        self.assertRaises(argparse.ArgumentTypeError):
                    validator(bad)

    def test_main_gives_usage_error_not_traceback(self):
        for args in (
            ["--challenges", "0"],
            ["--n-bits", "40"],
            ["--stage", "1", "--challenges", "2"],
            ["--fraction", "2"],
            ["--time-limit-ms", "0"],
            ["--stage", "2", "--threshold", "1"],
            ["--stage", "3", "--challenges", "1", "--threshold", "2"],
            ["--online-query-budget", "-1"],
        ):
            with self.subTest(args=args):
                run = subprocess.run([sys.executable, "main.py", *args], capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertIn("error:", run.stderr)
                self.assertNotIn("Traceback", run.stderr)

    def test_main_rejects_at_the_first_missing_answer(self):
        run = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--stage",
                "2",
                "--n-bits",
                "4",
                "--challenges",
                "3",
                "--challenge-seed",
                "3",
                "--time-limit-ms",
                "10",
                "--prover",
                "partial",
                "--fraction",
                "0.5",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn("1/3 answers valid", run.stdout)
        self.assertIn("Proof rejected (classified as adversary)", run.stdout)
        self.assertIn("Challenges attempted: 2/3", run.stdout)
        self.assertEqual(run.stdout.count(" y = "), 2)

    def test_trial_stops_after_a_timeout_or_an_invalid_answer(self):
        scheme = SimpleScheme(PoSParams(n_bits=4))
        prover = HonestProver(scheme)
        prover.setup()
        for elapsed, answer, status in ((0.01, 0, "timed out"), (0.0, -1, "rejected")):
            verifier = Verifier(scheme, max_response_time_ms=1)
            output = io.StringIO()
            with self.subTest(status=status), redirect_stdout(output), \
                    patch("pos.session.time.perf_counter", side_effect=(0, elapsed, elapsed, elapsed)), \
                    patch.object(verifier, "new_challenge", return_value=verifier.f(0)) as draw, \
                    patch.object(prover, "answer", return_value=answer) as respond:
                self.assertEqual(run_trials(prover, verifier, count=3, trials=1), 0)
                draw.assert_called_once()
                respond.assert_called_once()
            self.assertIn(status, output.getvalue())
            self.assertIn("classified as adversary", output.getvalue())

    def test_main_reports_trial_acceptance_and_bounded_search_work(self):
        run = subprocess.run(
            [sys.executable, "main.py", "--stage", "2", "--n-bits", "4", "--challenges", "4", "--trials", "2",
             "--prover", "timestorage", "--fraction", "0", "--online-query-budget", "1",
             "--challenge-seed", "1", "--time-limit-ms", "10"],
            capture_output=True, text=True,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Online prover evaluations: 2", run.stdout)
        self.assertIn("Trials accepted: 0/2", run.stdout)
        self.assertIn("Verification time: ", run.stdout)

    def test_main_accepts_honest_proof_when_all_challenges_pass(self):
        run = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--stage",
                "2",
                "--n-bits",
                "4",
                "--challenge-seed",
                "42",
                "--time-limit-ms",
                "1000",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(f"Challenges attempted: {STAGE_2_CHALLENGES}/{STAGE_2_CHALLENGES}", run.stdout)
        self.assertIn("Proof accepted", run.stdout)
        scheme = SimpleScheme(PoSParams(n_bits=4))
        function = scheme.new_function()
        rng = random.Random(42)
        expected = [function(rng.randrange(scheme.params.N)) for _ in range(STAGE_2_CHALLENGES)]
        self.assertEqual([int(line.split()[3]) for line in run.stdout.splitlines() if " y = " in line], expected)


if __name__ == "__main__":
    unittest.main()
