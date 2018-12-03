from unittest import TestCase

from math import gcd as _gcd

class Test_gcd(TestCase):

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
        
    
