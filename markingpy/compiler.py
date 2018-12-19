"""
Helper module to compile files that might contain syntax errors.
"""

# Based on the Python Standard Library code module.

import sys
from code import InteractiveInterpreter
from codeop import CommandCompiler



class Compiler:

    def __init__(self, source, filename='<input>', locals=None):
        self.locals = locals if locals else {}
        self.filename = filename
        
        self.lines = map(str.rstrip, source.splitlines())
        self.compile = CommandCompiler()
        self.syntax_errors = []
        self.code_blocks = []

        self.current_line = None
        self.lineno = 0

        self.reset_buffer(add_block=False)

    def reset_buffer(self, add_block=True):
        """
        Reset the input buffer.
        """
        if add_block and self.buffer:
            self.code_blocks.append(self.buffer)
        self.buffer = []

    def run(self, code):
        """
        Execute a code object
        """
        try:
            exec(code, self.locals)
        except SystemExit:
            raise
        except:
            print('Exception raised')
            print(*self.buffer,sep='\n', end='\n'+'='*70)
        
    def test_source(self, source, filename='<input>', symbol='single'):
        """
        Attempt to compile and run the command as though in an interpreter.
        """
        try:
            code = self.compile(source, filename, symbol)
        except IndentationError:
            print('Indentation Error', self.lineno)
            if self.code_blocks:
                self.code_blocks[-1].append(self.current_line)
            self.reset_buffer(add_block=False)
            return False
        except (OverflowError, SyntaxError, ValueError):
            self.syntax_errors.append(sys.exc_info())
            self.reset_buffer()
            return False

        if code is None:
            print(source, end='\n' + '='*70 + '\n')
            return True
        
       # print(source, end='\n' + '='*70 + '\n')

        self.run(code)
        self.reset_buffer()
        return False
                                      

    def push(self):
        source = '\n'.join(self.buffer)
        more = self.test_source(source, self.filename)
        return more

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.lineno += 1
            self.current_line = next(self.lines)
            self.buffer.append(self.current_line)
            self.push()
        except StopIteration:
            self.push()
            self.reset_buffer()
            raise
        return self.current_line
    
