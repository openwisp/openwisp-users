"""Verify the supported interface of the CI test entry point."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestCiEntrypoint(unittest.TestCase):
    def test_rejects_unsupported_arguments(self):
        for arguments in (
            ("--settings=other",),
            ("--testrunner=other.Runner",),
            ("--failfast",),
            ("openwisp_users.tests.test_missing",),
            ("openwisp_users.tests.test_models.User",),
            ("openwisp_users.tests.test_models", "openwisp2.sample_users.tests"),
        ):
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    ["./runtests", *arguments],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("Unsupported test argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
