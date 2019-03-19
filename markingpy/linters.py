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
"""
Code style analysis tools
"""
# TODO: This needs a rework. There is no real need for a new linter instance
#  to be created for every submission.
from pathlib import Path
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .import submission
from pylint.lint import PyLinter
from pylint.reporters.text import TextReporter

__all__ = ['LinterReport', 'linter']


class LinterReport:
    """
    Report class for collecting output of the linter.
    """

    def __init__(self):
        self.content = []
        self.stats = None

    def write(self, text: str):
        if not text.startswith("***"):
            self.content.append(text.strip())

    def read(self) -> str:
        if self.content:
            return "\n".join(self.content)

        else:
            return "No issues found"

    def set_stats(self, stats: Dict[str, int]):
        self.stats = stats


def linter(sub: 'submission.Submission') -> LinterReport:
    """
    Run the linter and generate a report for the submission.
    """
    report = LinterReport()
    linter = PyLinter()
    linter.load_default_plugins()
    linter.read_config_file()
    linter.load_config_file()
    args = (
        "--disable=C0103,C0111",
        "--persistent=n",
        '--msg-template="{line}:{column:2d}: {msg_id}: {msg}"',
    )
    linter.load_command_line_configuration(args)
    linter.set_reporter(TextReporter(report))
    path = Path("submission.py")
    path.write_text(sub.source)
    linter.check(path)
    report.set_stats(linter.stats)
    return report
