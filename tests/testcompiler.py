# Tests for compilers

from unittest import TestCase
from textwrap import dedent

from markingpy.compiler import Compiler


class TestCompiler(TestCase):

    def setUp(self):
        compiled_globals = {}
        self.compiled_globals = compiled_globals
        self.compiler = Compiler()

    def test_compile_good_code(self):
        """Test compiler compiles well-formed code correctly."""

        source = """
                 def test_func(a, b):
                    return a + b
                 
                 """
        source = dedent(source)
        code = self.compiler(source)
        exec(code, self.compiled_globals)

        self.assertIn('test_func', self.compiled_globals)

    def test_compile_malformed_code(self):
        """Test compilation of malformed code."""

        source = """
                 def bad_func(a, b):
                 return a + b

                 def good_func(a, b):
                     return a + b
                 """
        source = dedent(source)
        code = self.compiler(source)
        exec(code, self.compiled_globals)

        self.assertIn('good_func', self.compiled_globals)
        self.assertNotIn('bad_func', self.compiled_globals)

    def test_function_with_extra_whitespace(self):
        """Test a function with extra whitespace in a function."""
        source = dedent('''
                        def long_function(a, b):
                            # Function starts here.




                            
                            # and ends here.
                            return a + b
                        ''')
        
        code = self.compiler(source)
        exec(code, self.compiled_globals)
        self.assertIn('long_function', self.compiled_globals)
        self.assertEqual(self.compiled_globals['long_function'](1,1), 2)

