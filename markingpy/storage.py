from os.path import exists as pathexists
import csv
import sqlite3
import atexit
import logging

logger = logging.getLogger(__name__)


class Database:

    def __init__(self, path, markscheme_id):
        self.path = path
        parent = path.parent
        if not parent.exists():
            logger.debug(f'Creating directory {parent}')
            parent.mkdir(parents=True)
        self.markscheme_id = markscheme_id
        self.db = db = sqlite3.connect(str(self.path))
        self.create_table()
        atexit.register(db.close)

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

    def insert(self, submission_id, percentage, feedback):
        db = self.db
        db.execute(
            "INSERT OR REPLACE INTO"
            " submissions ("
            " submission_id,"
            " percentage,"
            " feedback,"
            " markscheme_id"
            ") VALUES (?, ?, ?, ?)",
            (submission_id, percentage, feedback, self.markscheme_id),
        )
        db.commit()

    def query(self, submission_id):
        cur = self.db.execute(
            "SELECT submission_id, percentage, feedback"
            " FROM submissions WHERE"
            " markscheme_id = ? AND"
            " submission_id = ?",
            (self.markscheme_id,
            submission_id,)
        )
        return cur.fetchone()

    def fetch_all(self):
        cur = self.db.execute(
            "SELECT submission_id, percentage, feedback"
            " FROM submissions WHERE"
            " markscheme_id = ?",
            (self.markscheme_id,)
        )
        return cur.fetchall()


_DATABASE = None


def get_db(path, markscheme_id):
    global _DATABASE
    logger.debug(f'Getting database from path: {str(path)}')
    if _DATABASE is None:
        _DATABASE = Database(path, markscheme_id)
    return _DATABASE


def write_csv(
    store_path, submissions, id_heading="Submission ID", score_heading="Score"
):
    if pathexists(store_path):
        raise RuntimeError(
            "Path %s already exists" ", cannot write" % store_path
        )

    with open(store_path, "w") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=[id_heading, score_heading]
        )
        writer.writeheader()

        def submission_to_dict(submission):
            return {
                id_heading: submission.reference,
                score_heading: submission.score,
            }

        for item in map(submission_to_dict, submissions):
            writer.writerow(item)
