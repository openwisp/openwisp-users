"""Verify the supported interface of the CI test entry point."""

import os
import runpy
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_focused_labels_select_their_configuration(self):
        runner = runpy.run_path(str(ROOT / "runtests.py"))["run_focused_tests"]
        for label, sample in (
            ("openwisp_users.tests.test_models.TestUsers.test_user_get_pk", ""),
            ("testapp.tests.tests.TestIntegration.test_validate_org_relation", ""),
            ("openwisp2.sample_users.tests.TestUsers.test_user_get_pk", "1"),
        ):
            with self.subTest(label=label), patch.dict(
                os.environ, {"SAMPLE_APP": ""}
            ), patch.object(sys, "argv", ["runtests.py"]), patch(
                "django.setup"
            ), patch.dict(
                runner.__globals__, {"validate_test_labels": lambda labels: None}
            ):
                runner([label, "--noinput"])
                self.assertEqual(os.environ["SAMPLE_APP"], sample)
                self.assertEqual(sys.argv[1:], ["test", label, "--noinput"])


if __name__ == "__main__":
    unittest.main()
