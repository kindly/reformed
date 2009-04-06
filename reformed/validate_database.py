from migrate.versioning import schemadiff
from custom_exceptions import DatabaseInvalid

import reformed

def check_tables(database):
    """ see if there is a differenct beteen the defined tables and the 
    database"""
    
    diff = schemadiff.getDiffOfModelAgainstDatabase(database.metadata,
                                                    database.engine) 
    if diff.tablesMissingInDatabase:
        missing_tables = [] 
        for table in diff.tablesMissingInDatabase:
            missing_tables.append(table.name)
        raise DatabaseInvalid("Tables not in the database \n %s" % missing_tables)

    #TODO decide if this is needed, or if its logged
    if diff.tablesMissingInModel:
        missing_tables = [] 
        for table in diff.tablesMissingInModel:
            missing_tables.append(table.name)
        print "Warning: Tables in database not used %s" % missing_tables

def check_fields(database):
    pass

def validate_database(database):

    check_tables(database)

#['__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__', '__hash__', '__init__', '__len__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__weakref__', 'colDiffs', 'compareModelToDatabase', 'conn', 'excludeTables', 'model', 'reflected_model', 'storeColumnDiff', 'storeColumnMissingInDatabase', 'storeColumnMissingInModel', 'tablesMissingInDatabase', 'tablesMissingInModel', 'tablesWithDiff']
