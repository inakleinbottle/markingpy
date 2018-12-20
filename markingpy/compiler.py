"""
Helper module to compile files that might contain syntax errors.
"""

# Based on the Python Standard Library code module.

import sys
from code import InteractiveInterpreter
from io import StringIO


class Compiler(InteractiveInterpreter):
    """
    Source code compiler that compiles all syntactically correct
    source code and populates a local namespace.
    
    Arugments:
        filename - A string containing the name of the origin of
                   the source code.
        locals - A dictionary to be populated with the names
                 defined in the provided source.
    
    Attributes:
        filename
        locals
        report - A string buffer containing the traceback for any
                 errors encountered during compilation.
    
    Methods:
        reset_buffer
        write
        push
        compile_source
        
    """

    def __init__(self, filename, locals):
        """
        Constructor.
        
        """
        super().__init__(locals)
        self.filename = filename
        self.reset_buffer()
        self.report = StringIO()

    def reset_buffer(self):
        """
        Reset the input buffer.
        """
        self.buffer = []

    def write(self, data):
        """
        Write compilation errors to the internal buffer.

        Arguments:
            data - string data to write.
        """
        self.report.write(data)

    def push(self, line):
        """
        Push a line to the interpreter.
        
        Arguments:
            line - String to be processed.
        """
        self.buffer.append(line)
        source = '\n'.join(self.buffer)
        more = self.runsource(source, self.filename)
        if not more:
            self.reset_buffer()
        return more

    def compile_source(self, source):
        """
        Compile the source ignoring any compilation errors.

        Populate the compiler's locals dictionary with the
        variables defined in source. Any code containing
        syntax errors will not be compiled, and those names
        will not be contained in the locals.

        Arguments:
            Source - string containing source to be compiled.
        """
        for line in source.splitlines():
            self.push(line.rstrip())
        # Push one final blank line to ensure the final buffer
        # is executed
        self.push('')
