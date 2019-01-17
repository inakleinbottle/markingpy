# Test submission objects
from unittest import TestCase
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from textwrap import dedent


from markingpy.submission import Submission
from markingpy.utils import build_style_calc


class TestStyleCalculator(TestCase):
    def test_style_calc_builder(self):
        """Test the style calculator factory."""

        test_dict = {
            "error": 1,
            "warning": 2,
            "refactor": 0,
            "convention": 4,
            "statement": 15,
        }

        calc = build_style_calc(
            "(error + warning + refactor + convention)" "/statement"
        )
        mock = MagicMock()
        mock.stats = test_dict

        self.assertEqual(calc(mock), 7 / 15)


class TestSubmissionClass(TestCase):
    def setUp(self):
        self.submission = Submission("testpath", "")

    def test_compilation_of_source(self):
        """Test compilation of good source code."""
        source = """
        def func_1():
            pass
        """
        self.submission.source = self.submission.raw_source = dedent(source)
        compile_mock = MagicMock(return_value=(None, None))
        compile_mock.removed_chunks = []
        self.submission.compiler = compile_mock

        self.submission.compile()

        compile_mock.assert_called_with(dedent(source))
        self.assertIn("compilation", self.submission.feedback)
        self.assertEqual(
            self.submission.feedback["compilation"],
            "No compilation errors found.",
        )

    def test_compilation_tab_error(self):
        """
        Test compilation of source containing tab errors.
        """
        source = dedent(
            """
        def good_fun():
            return None
        
        def bad_fun():
        \treturn None
        """
        )

        self.submission.source = self.submission.raw_source = source
        compile_mock = MagicMock(return_value=(None, None))
        removed_chunk = MagicMock()
        err = MagicMock()
        err.exc = "TabError"
        removed_chunk.get_first_error = MagicMock(return_value=err)
        removed_chunk.content = dedent(
            """\
        def bad_fun():
        \treturn None"""
        )
        compile_mock.removed_chunks = [removed_chunk]

        self.submission.compiler = compile_mock

        self.submission.compile()

        compile_mock.assert_called_with(dedent(source))
        self.assertIn("compilation", self.submission.feedback)
        self.assertIsInstance(self.submission.feedback["compilation"], str)

    def test_generate_report_no_compile(self):
        """Test compilation fails with non-compiled submission."""
        self.assertRaises((RuntimeError,), self.submission.generate_report)

    def test_generate_report_no_score(self):
        """Test compilation fails with non-graded submission."""
        self.submission.code = True
        self.assertRaises((RuntimeError,), self.submission.generate_report)

    def test_generation_of_report(self):
        """Test successful compilation of support."""
        self.submission.code = True
        self.submission.score = 1
        self.assertIsInstance(self.submission.generate_report(), str)
