
import reformed.data_loader
import os

TABLES = ['_core', 'comment', 'user', 'severity', 'priority', 'ticket', 'bookmarks', 
          'permission', 'user_group', 'user_group_permission', 'user_group_user', 'code', 'code_type']

def load(application):

    application.initialise_database()

    database = application.database
    application_folder = application.application_folder
    data_folder = os.path.join(application_folder, "data")

    for table in database.metadata.sorted_tables:
        if table.name in TABLES:
            print table.name
            try:
                flatfile = reformed.data_loader.FlatFile(
                    database,
                    table.name,
                    os.path.join(data_folder, "%s.csv" % table.name),
                    from_load = True
                )
                flatfile.load()
            except IOError:
                pass
