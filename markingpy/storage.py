from os.path import exists as pathexists
import csv


def write_csv(store_path, submissions, 
              id_heading='Submission ID', score_heading='Score'):
    if pathexists(store_path):
        raise RuntimeError('Path %s already exists'
                           ', cannot write' % store_path)

    with open(store_path, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[id_heading, score_heading])
        writer.writeheader()

        def submission_to_dict(submission):
            return {id_heading : submission.reference,
                    score_heading : submission.score}

        for item in map(submission_to_dict, submissions):
            writer.writerow(item)




