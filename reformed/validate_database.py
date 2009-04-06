from migrate.versioning import schemadiff
from custom_exceptions import DatabaseInvalid

import reformed

def check_tables(database, diff):
    """ see if there is a difference beteen the defined tables and the 
    database"""
    missing_database = [] 
    missing_definition = [] 
    
    if diff.tablesMissingInDatabase:
        for table in diff.tablesMissingInDatabase:
            missing_database.append(table.name)
        raise DatabaseInvalid("Defined tables are not in the database \n %s" % missing_database, 
                              missing_database)

    #TODO decide if this is needed, or if its logged
    if diff.tablesMissingInModel:
        for table in diff.tablesMissingInModel:
            missing_definition.append(table.name)
        print "Warning: Tables in database not used %s" % missing_definition

    return [missing_database, missing_definition]

def check_fields(database, diff):

    missing_in_database = []
    missing_in_definition = []
    different =[]

    for name, table in diff.colDiffs.iteritems():
        for missing in table[0]:
            missing_in_database.append("%s.%s" % (name, missing.name))
        for missing in table[1]:
            missing_in_definition.append("%s.%s" % (name, missing.name))
        for diff in table[2]:
            different.append("%s.%s" % (name, diff[0].name))
    pass
    
    if missing_in_database:
        raise DatabaseInvalid("Defined fields are not in database %s" % missing_in_database,
                              missing_in_database)

    if missing_in_definition:
        print "Warning: Fields in database not used %s" % missing_in_definition

    if different:
        print "Warning: These fields are different than the database %s" % diff

    return [missing_in_database, missing_in_definition, different]

def validate_database(database):

    diff = schemadiff.getDiffOfModelAgainstDatabase(database.metadata,
                                                    database.engine) 
    all_diff = []

    tables_diff = check_tables(database, diff)
    fields_diff = check_fields(database, diff)

    all_diff.extend(tables_diff)
    all_diff.extend(fields_diff)

    return all_diff


#['__class__', '__delattr__', '__dict__', '__doc__', '__getattribute__', '__hash__', '__init__', '__len__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__weakref__', 'colDiffs', 'compareModelToDatabase', 'conn', 'excludeTables', 'model', 'reflected_model', 'storeColumnDiff', 'storeColumnMissingInDatabase', 'storeColumnMissingInModel', 'tablesMissingInDatabase', 'tablesMissingInModel', 'tablesWithDiff']
