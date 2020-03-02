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
#
"""
Grading tool for python files.
"""

import abc
import logging
import multiprocessing as mp
from collections import namedtuple

logger = logging.getLogger(__name__)
__all__ = ['SimpleGrader', 'ProcessGrader', "Record"]
Record = namedtuple('Record', ('id', 'score', 'feedback'))


class GraderABC(abc.ABC):
    """
    Abstract base class for graders.
    """

    @abc.abstractmethod
    def submit(self, task, submission):
        """
        Submit a task to the grader

        :param task: Grading task to complete
        :return:
        """
        pass

    @abc.abstractmethod
    def set_db(self, db):
        """
        Set the database.

        :param db:
        :return:
        """
        pass


class SimpleGrader(GraderABC):
    """
    Simple grader class. Grading tasks are completed in process.
    """

    def __init__(self):
        logger.info("Creating SimpleGrader instance")
        self.db = None

    def submit(self, task, submission):
        result = task(submission.compile())
        mark = sum(res.marks for res in result)
        total_mark = sum(res.total_marks for res in result)
        feedback = '\n'.join(res.feedback for res in result)
        submission.add_feedback('tests', feedback)
        if self.db:
            self.db.add_record(
                Record(submission.reference, mark * 100 / total_mark, feedback)
            )

    def set_db(self, db):
        self.db = db


def _task_worker(task, code, result):
    result.value = task(code)


class ProcessGrader(GraderABC):
    """
    Grader that runs each grading task in a separate process, thus
    providing runtime isolation. However, this incurs additional
    resource costs and is significantly slower than a simple grader.
    """

    def __init__(self, method=None):
        self.context = ctx = mp.get_context(method)
        self.manager = ctx.Manager()
        self.task_id = 0
        self.db = None

    def submit(self, task, submission):
        self.task_id += 1
        result = self.manager.Value(f'result-{self.task_id}', None)
        proc = self.context.Process(
            target=_task_worker, args=(task, submission.compile(), result)
        )
        proc.start()
        proc.join()
        mark = sum(res.marks for res in result.value)
        total_mark = sum(res.total_marks for res in result.value)
        feedback = '\n'.join(res.feedback for res in result.value)
        submission.add_feedback('tests', feedback)
        if self.db:
            self.db.add_record(
                Record(submission.reference, mark * 100 / total_mark, feedback)
            )

    def set_db(self, db):
        self.db = db
