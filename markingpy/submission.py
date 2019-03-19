#      Markingpy automatic grading tool for Python code.
#      Copyright (C) 2019 University of East Anglia
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import os
import logging
from collections import namedtuple
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import CodeType
from .compiler import Compiler
from .utils import log_calls

logger = logging.getLogger(__name__)
# INDENT = ' '*4
Scores = namedtuple("Scores", ["raw", "total", "percentage", "formatted"])
__all__ = ['Submission']


class Submission:

    def __init__(self, reference: str, source: str, **kwargs: Any):
        self.reference = reference
        self.compiler = Compiler()
        self.source = self.raw_source = source
        self.code = None
        self.score = None
        self.percentage = 0
        self.feedback = {}

    @log_calls
    def compile(self) -> 'CodeType':
        """
        Compile the submission source code.
        """
        if not self.code:
            self.source, self.code = self.compiler(self.raw_source)
            if self.compiler.removed_chunks:
                feedback = "\n".join(
                    (
                        "Removed:\n" +
                        c.content +
                        "\n" +
                        str(c.get_first_error().exc)
                        for c in self.compiler.removed_chunks
                    )
                )
            else:
                feedback = "No compilation errors found."
            self.add_feedback("compilation", feedback)
        return self.code

    @log_calls
    def add_feedback(self, item: str, feedback: str):
        """
        Add feedback to the submission.
        """
        self.feedback[item] = feedback

    def generate_report(self) -> str:
        """
        Generate report for this submission.
        """
        if not self.code:
            raise RuntimeError("Submission has not yet been compiled.")

        if not self.score:
            raise RuntimeError("Submission has not yet been graded.")

        lines = [
            "Result summary for submission {}".format(self.reference),
            "\nCompilation report:",
            self.feedback.get("compilation", ""),
            "\nResults for exercises:",
            self.feedback.get("tests", ""),
            "\nResults of style analysis:",
            self.feedback.get("style", ""),
            "\n" + "=" * 70 + "\n",
            "Final score {}".format(self.score),
        ]
        return "\n".join(lines)
