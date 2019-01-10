import pytest

import markingpy.grader
from markingpy.grader import Grader, import_markscheme




def test_mark_scheme_imported(self, monkeypatch):
    """Test importing of markscheme."""

    class ms:
        def get_submissions(self):
            return ['Submissions']

    def patched_import(file):
        assert file == 'test_file'
        return ms()
    monkeypatch.setattr(markingpy.grader, import_markscheme, patched_import)
    grader = Grader('test_file')
    assert isinstance(grader.markscheme, ms)
    assert list(grader.submissions) == ['Submissions']


