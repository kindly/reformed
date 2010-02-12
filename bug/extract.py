
import csv
import os

def extract(database, dir):

    this_dir = os.path.dirname(os.path.abspath(__file__))
    application_folder = os.path.join(this_dir, dir)
    data_folder = os.path.join(this_dir, "data")

    for table in database.tables:
        print 'extracting ', table
        results = database.search(table, tables = [table])["data"]
        with file(os.path.join(data_folder, "%s.csv" % table), mode = "w+") as out_file:
            csv_file = csv.writer(out_file,quoting=csv.QUOTE_ALL)

            if not results:
                rows = database[table].columns.keys() + ["id"]
                csv_file.writerow(database[table].columns.keys() + ["id"])
                continue

            columns = results[0].keys()
            columns.remove("__table")
            columns.remove("_version")
            csv_file.writerow(columns)

            for row in results:
                out = []
                for column in columns:
                    out.append(row[column])

                csv_file.writerow(out)

