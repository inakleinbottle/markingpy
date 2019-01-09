import unittest
from unittest import mock
from textwrap import dedent

from markingpy.markscheme import mark_scheme, import_markscheme, MarkingScheme


class ImportMarkschemeTests(unittest.TestCase):

    def setUp(self):
        source = '''\
        from markingpy import mark_scheme, exercise
        
        ms = mark_scheme()
        
        @exercise
        def exercise_1():
            pass
        '''

        patcher = mock.patch('markingpy.markscheme.open',
                             mock.mock_open(read_data=dedent(source)))
        self.mock_open = patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch('markingpy.markscheme.build_style_calc')
    def test_import_marksheme(self, mock_style_calc):
        """Test that mark scheme object correctly created and imported."""
        markscheme = import_markscheme('testpath')
        self.mock_open.assert_called_with('testpath', 'rt')
        mock_style_calc.assert_called()


if __name__ == '__main__':
    unittest.main()
