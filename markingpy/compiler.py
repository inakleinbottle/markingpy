"""
Helper module to compile files that might contain syntax errors.
"""

# Based on the Python Standard Library code module.

from codeop import PyCF_DONT_IMPLY_DEDENT
from collections import namedtuple, deque


# Chunk = namedtuple('Chunk', ('line_start', 'line_end', 'content'))
Reason = namedtuple("Reason", ("removed_at", "exc"))


class Chunk:

    __slots__ = ["line_start", "line_end", "content"]

    def __init__(self, line_start, line_end, content):
        self.line_start = line_start
        self.line_end = line_end
        self.content = content

    def __iter__(self):
        yield from (self.line_start, self.line_end, self.content)

    def __repr__(self):
        return (
            self.__class__.__name__
            + "("
            + repr(self.line_start)
            + repr(self.line_end)
            + repr(self.content)
            + ")"
        )


class RemovedChunk(Chunk):

    __slots__ = ["line_start", "line_end", "content", "reasons"]

    def __init__(self, line_start, line_end, content):
        super().__init__(line_start, line_end, content)
        self.reasons = []

    def is_adjacent(self, other):
        return (
            abs(other.line_end - self.line_start) <= 1
            or abs(other.line_start - self.line_end) <= 1
        )

    def add_reason(self, *reason):
        rm_list = [r.removed_at for r in self.reasons]
        for r in reason:
            if not r.removed_at in rm_list:
                self.reasons.append(r)

    def join(self, other):
        if self.line_start > other.line_end:
            # other first
            content = "\n".join([other.content, self.content])
            start = other.line_start
            end = self.line_end
        else:
            # this first
            content = "\n".join([self.content, other.content])
            start = self.line_start
            end = other.line_end
        new_removed = RemovedChunk(start, end, content)
        new_removed.add_reason(*self.reasons, *other.reasons)
        return new_removed

    def get_first_error(self):
        return min(self.reasons, key=lambda r: r.removed_at)


class Compiler:
    """
    Source code compiler that compiles all syntactically correct
    source code and populates a local namespace.
    
    Arugments:
        filename - A string containing the name of the origin of
                   the source code.
        locals - A dictionary to be populated with the names
                 defined in the provided source.
        
    """

    def __init__(self, filename="<input>", mode="exec"):
        """
        Constructor.
        """
        self.filename = filename
        self.mode = mode
        self.removed_chunks = []
        self.chunks = []
        self.removed = 0
        self.to_process = deque()

    def __call__(
        self,
        source,
        *,
        filename="<input>",
        mode="exec",
        flags=0,
        dont_inherit=False,
        optimize=-1
    ):
        return self.compile_source(
            source, filename, mode, flags, dont_inherit, optimize
        )

    def remove_line(self, chunk, lineno, reason):
        """
        Remove a line from the source.
        """
        lines = chunk.content.splitlines()
        reason.lineno = chunk.line_start + lineno - 1
        self.removed += 1

        removed_chunk = RemovedChunk(
            reason.lineno, reason.lineno, lines[lineno - 1]
        )
        removed_chunk.add_reason(Reason(self.removed, reason))
        adjacent = [
            c for c in self.removed_chunks if c.is_adjacent(removed_chunk)
        ]
        if not adjacent:
            self.removed_chunks.append(removed_chunk)
        else:
            for c in adjacent:
                removed_chunk = c.join(removed_chunk)
                self.removed_chunks.remove(c)
            self.removed_chunks.append(removed_chunk)

        # print('Removing line', reason.lineno, lines[lineno-1])
        return (
            Chunk(
                chunk.line_start, lineno - 2, "\n".join(lines[: lineno - 1])
            ),
            Chunk(reason.lineno, chunk.line_end, "\n".join(lines[lineno:])),
        )

    def try_compile(self, chunk):
        """
        Try compiling a chunk.
        """
        try:
            # noinspection PyArgumentList
            compile(
                chunk.content,
                self.filename,
                self.mode,
                PyCF_DONT_IMPLY_DEDENT,
                optimize=0,
            )
            self.chunks.append(chunk)
        except SyntaxError as err:
            self.handle_compile_exception(err, chunk)

    def handle_compile_exception(self, err, chunk):
        """
        Handle an exception raised during compilation.
        """
        lineno = err.lineno
        before, after = self.remove_line(chunk, lineno, err)
        if before.content:
            self.to_process.append(before)
        if after.content:
            self.to_process.append(after)

    def compile_source(
        self, source, filename, mode, flags, dont_inherit, optimize
    ):
        """
        Compile the source ignoring any compilation errors.

        Populate the compiler's locals dictionary with the
        variables defined in source. Any code containing
        syntax errors will not be compiled, and those names
        will not be contained in the locals.

        Arguments:
            Source - string containing source to be compiled.
        """
        self.to_process.append(Chunk(0, len(source.splitlines()), source))
        while self.to_process:
            self.try_compile(self.to_process.popleft())
        self.sort_chunks()
        new_source = "\n".join(map(lambda c: c.content, self.chunks))
        # noinspection PyArgumentList
        return compile(
            new_source, filename, mode, flags, dont_inherit, optimize
        )

    def sort_chunks(self):
        self.chunks.sort(key=lambda c: c.line_start)
