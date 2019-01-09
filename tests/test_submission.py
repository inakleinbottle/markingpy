# Test submission objects
from unittest import TestCase
from unittest.mock import MagicMock
from markingpy.utils import build_style_calc



class TestStyleCalculator(TestCase):

    def test_style_calc_builder(self):
        """Test the style calculator factory."""

        test_dict = {'error': 1,
                     'warning': 2,
                     'refactor': 0,
                     'convention': 4,
                     'statement': 15
                    }

        calc = build_style_calc('(error + warning + refactor + convention)'
                                '/statement')
        mock = MagicMock()
        mock.stats = test_dict

        self.assertEqual(calc(mock), 7/15)




