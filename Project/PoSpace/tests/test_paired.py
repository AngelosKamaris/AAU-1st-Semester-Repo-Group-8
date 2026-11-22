"""Correctness tests for the paired construction."""

import hashlib
import random
import subprocess
import sys
import unittest

from pos import PoSParams, Verifier
from pos.functions import pi
from pos.provers.time_storage import PairedTimeStorageProver
from pos.schemes import SimpleScheme
from pos.schemes.paired import PairedScheme


class TestPaired(unittest.TestCase):
    def setUp(self):
        self.params = PoSParams(n_bits=5, seed=3, seed_g=7)
        self.scheme = PairedScheme(self.params)
        self.function = self.scheme.new_function()

    def test_involution_and_unchanged_f(self):
        simple = SimpleScheme(self.params).new_function()
        for value in range(self.params.N):
            complement = pi(value, self.params.n_bits)
            self.assertNotEqual(value, complement)
            self.assertEqual(pi(complement, self.params.n_bits), value)
            self.assertEqual(self.function.f(value), simple(value))

    def test_g_uses_ordered_fixed_width_inputs_and_its_own_key(self):
        function = PairedScheme(PoSParams(n_bits=9, seed_g=7)).new_function()
        for first, second in ((1, 258), (258, 1)):
            encoded = first.to_bytes(2, "big") + second.to_bytes(2, "big")
            digest = hashlib.blake2b(encoded, key=b"g" + (7).to_bytes(16, "big")).digest()
            self.assertEqual(function.g(first, second), int.from_bytes(digest[:2], "big") >> 7)

    def test_plot_matches_exhaustive_ordered_pair_reference(self):
        domain = range(self.params.N)
        forward = [self.function.f(value) for value in domain]
        mask = self.params.N - 1
        pairs = {(first, second) for first in domain for second in domain
                 if forward[first] ^ forward[second] == mask}
        outputs = {self.function.g(*pair) for pair in pairs}
        plot_function = self.scheme.new_function()
        plot = self.scheme.build_plot(plot_function)
        self.assertEqual(plot_function.f.calls, self.params.N)
        self.assertEqual(plot.pair_count, len(pairs))
        self.assertEqual(plot.unpaired, self.params.N - len({first for first, _ in pairs}))
        self.assertEqual(len(plot), len(outputs))
        verifier = Verifier(self.scheme)
        for challenge in domain:
            answer = plot.lookup(challenge)
            self.assertEqual(verifier.check(challenge, answer), challenge in outputs)
            if challenge not in outputs:
                self.assertIsNone(answer)

    def test_verifier_checks_both_conditions_and_samples_without_the_plot(self):
        rng = random.Random(42)
        verifier = Verifier(self.scheme, rng_seed=42)
        for _ in range(self.params.N):
            self.assertEqual(verifier.new_challenge(), rng.randrange(self.params.N))
        self.assertEqual(verifier.f.calls, 0)
        plot = self.scheme.build_plot(self.function)
        challenge = next(value for value in range(self.params.N) if plot.lookup(value) is not None)
        answer = plot.lookup(challenge)
        first, second = answer
        self.assertTrue(verifier.check(challenge, answer))
        self.assertFalse(verifier.check((challenge + 1) % self.params.N, answer))
        self.assertFalse(verifier.check(self.function.g(first, first), (first, first)))
        for invalid in ((True, second), (first, self.params.N), (first,), None):
            self.assertFalse(verifier.check(challenge, invalid))

    def test_recovery_obeys_combined_budget_and_does_not_cache(self):
        plot = self.scheme.build_plot(self.function)
        present = next(value for value in range(self.params.N) if plot.lookup(value) is not None)
        absent = next(value for value in range(self.params.N) if plot.lookup(value) is None)
        for fraction, budget, challenge, expected_work in ((1, 0, present, 0), (0, 0, present, 0),
                                                            (0, 10, absent, 10), (0, 40, absent, 40)):
            prover = PairedTimeStorageProver(self.scheme, fraction, online_query_budget=budget)
            prover.setup()
            before = prover.queries
            answer = prover.answer(challenge)
            self.assertEqual(prover.queries - before, expected_work)
            self.assertEqual(answer, plot.lookup(challenge) if fraction else None)

        prover = PairedTimeStorageProver(self.scheme, 0)
        prover.setup()
        verifier = Verifier(self.scheme)
        work = []
        for _ in range(2):
            before = prover.queries
            self.assertTrue(verifier.check(present, prover.answer(present)))
            work.append(prover.queries - before)
        self.assertEqual(len(prover.plot), 0)
        self.assertEqual(work[0], work[1])
        self.assertGreater(work[0], 0)

    def test_cli_measures_coverage_before_an_explicit_threshold(self):
        args = [sys.executable, "main.py", "--stage", "3", "--n-bits", "5", "--seed-f", "3",
                "--seed-g", "7", "--challenges", "10", "--challenge-seed", "42"]
        pilot = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(pilot.returncode, 0, pilot.stderr)
        self.assertIn("plot coverage:", pilot.stdout)
        self.assertNotIn("Trials accepted:", pilot.stdout)
        plot = self.scheme.build_plot(self.function)
        rng = random.Random(42)
        valid = sum(plot.lookup(rng.randrange(self.params.N)) is not None for _ in range(10))
        self.assertIn(f"Valid answers: {valid}/10", pilot.stdout)
        for threshold, exit_code in ((valid, 0), (valid + 1, 1)):
            scored = subprocess.run([*args, "--threshold", str(threshold)], capture_output=True, text=True)
            self.assertEqual(scored.returncode, exit_code, scored.stderr)
