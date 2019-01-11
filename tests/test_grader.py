from pathlib import Path
from collections.abc import Iterable

import pytest

import markingpy.grader
from markingpy.grader import Grader


def test_mark_scheme_imported(monkeypatch):
    """Test importing of markscheme."""

    class ms:
        def get_submissions(self):
            return ["Submissions"]

    def patched_import(file):
        return ms()

    monkeypatch.setattr(markingpy.grader, "import_markscheme", patched_import)
    grader = Grader(Path("test_file"))
    assert isinstance(grader.markscheme, ms)
    assert isinstance(grader.submissions, Iterable)
