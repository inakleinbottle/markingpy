

from math import gcd as _gcd

from markingpy import Exercise, mark_scheme

mark_scheme(
    style=10.,
    test=90.
    )

class Test_gcd(Exercise):

    names = ['gcd']

    def test_gcd_1(self):
        """gcd with inputs 12, 16; expected 4
        """
        self.assertEqual(gcd(12, 16), _gcd(12, 16))
        
    def test_gcd_2(self):
        """gcd with inputs 52, 76; expected
        """
        self.assertEqual(gcd(52, 76), _gcd(52, 76))
    
    def test_gcd_3(self):
        """gcd with inputs 264, 328; expected 8
        """
        self.assertEqual(gcd(264, 328), _gcd(264, 328))
        
    
