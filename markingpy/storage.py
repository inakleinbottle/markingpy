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
from os.path import exists as pathexists
import csv
import abc
import sqlite3
import atexit
import logging

from .grader import Record

logger = logging.getLogger(__name__)
__all__ = ['StorageABC', 'SQLiteDB']


class StorageABC(abc.ABC):

    @abc.abstractmethod
    def add_record(self, record):
        """
        Add a record to the database.

        :param record:
        :return:
        """
        pass

    @abc.abstractmethod
    def get_record(self, record_id):
        """
        Get a record from the database.

        :param record_id:
        :return:
        """
        pass

    @abc.abstractmethod
    def get_all(self):
        """
        Get all records from the database.

        :return:
        """


class CSVStorageDB(StorageABC):
    """
    Store grades in a CSV file.
    """

    def __init__(self, path):
        self.path = path
        self.mode = None
        self.csv = None
        self.raw_file = None

    def open_for_read(self):
        if self.mode == "read":
            raise RuntimeError("Cannot open for reading, file is open for writing")

        self.raw_file = f = open(self.path, 'w')
        atexit.register(f.close)
        self.csv = csv.DictReader(f, ("submission_id", "percentage"))
        self.mode = "read"

    def open_for_write(self):
        if self.mode == "read":
            raise RuntimeError("Cannot open for writing, file is open for reading")

        self.raw_file = f = open(self.path, 'w')
        atexit.register(f.close)
        self.csv = csv.DictWriter(f, ("submission_id", "percentage"))
        self.mode = "write"

    def close_file(self):
        if self.raw_file is None:
            raise RuntimeError("File is not open")

        self.raw_file.close()
        atexit.unregister(self.raw_file.close)
        self.mode = None

    def add_record(self, record):
        if not self.mode == "write":
            self.open_for_write()
        self.csv.writerow({"submission_id": record.id, "percentage": record.score})

    def get_record(self, record_id):
        if not self.mode == "read":
            self.open_for_read()
        for row in self.csv:
            if row["submission_id"] == record_id:
                return Record(row["submission_id"], row["percentage"], "")

        raise RuntimeError(f"No record found for id {record_id}")

    def get_all(self):
        if not self.mode == "read":
            self.open_for_read()
        return map( lambda r: Record(r["submission_id"], r["percentage"], ""), self.csv)


class SQLiteDB(StorageABC):

    def __init__(self, path):
        self.path = path
        parent = path.parent
        if not parent.exists():
            logger.debug(f"Creating directory {parent}")
            parent.mkdir(parents=True)
        self.db = db = sqlite3.connect(str(path))
        atexit.register(db.close)
        self.create_table()

    def create_table(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS submissions ("
            " submission_id text primary key,"
            " percentage int,"
            " feedback text,"
            " markscheme_id text"
            ");"
        )
        self.db.commit()

    def add_record(self, record):
        self.db.execute(
            "INSERT OR REPLACE INTO"
            " submissions ("
            " submission_id,"
            " percentage,"
            " feedback,"
            ") VALUES (?, ?, ?)",
            (record.id, record.score, record.feedback),
        )
        self.db.commit()

    def get_record(self, record_id):
        cur = self.db.execute(
            "SELECT submission_id, percentage, feedback"
            " FROM submissions WHERE"
            " submission_id = ?",
            (record_id,),
        )
        return cur.fetchone()

    def get_all(self):
        cur = self.db.execute(
            "SELECT submission_id, percentage, feedback" " FROM submissions"
        )
        return cur.fetchall()


def write_csv(
    store_path, submissions, id_heading="Submission ID", score_heading="Score"
):
    if pathexists(store_path):
        raise RuntimeError("Path %s already exists" ", cannot write" % store_path)

    with open(store_path, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[id_heading, score_heading])
        writer.writeheader()

        def submission_to_dict(submission):
            return {id_heading: submission.reference, score_heading: submission.score}

        for item in map(submission_to_dict, submissions):
            writer.writerow(item)
