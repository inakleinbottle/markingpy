from os.path import exists as pathexists
import csv
import sqlite3
import atexit


class Database:
    def __init__(self, path):
        self.path = path
        create_table = True if not path.exists() else False
        self.db = db = sqlite3.connect(str(self.path))
        atexit.register(db.close)
        if create_table:
            self.create_table()

    def create_table(self):
        self.db.execute(
            "CREATE TABLE submissions ("
            " submission_id text primary key,"
            " percentage int,"
            " feedback text"
            ");"
        )
        self.db.commit()

    def insert(self, submission_id, percentage, feedback):
        db = self.db
        db.execute(
            "INSERT INTO submissions (submission_id, percentage, feedback)"
            " VALUES (?, ?, ?)",
            (submission_id, percentage, feedback),
        )
        db.commit()

    def query(self, submission_id):
        cur = self.db.execute(
            "SELECT * FROM submissions " "WHERE submission_id = ?",
            submission_id,
        )
        return cur.fetchone()

    def fetch_all(self):
        cur = self.db.execute(
            "SELECT * FROM submissions"
        )
        return cur.fetchall()


_DATABASE = None


def get_db(path):
    global _DATABASE
    if _DATABASE is None:
        _DATABASE = Database(path)
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
