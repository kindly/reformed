import sqlalchemy as sa
import custom_exceptions

class Database(object):
    
    def __init__(self,name,*args,**kw):
        self.name =name
        self.tables = {}
        self.metadata = kw.pop("metadata",None)
        for tables in args:
            tables._set_parent(self)

    @property
    def relations(self):
        relations = []
        for table_name,table_value in self.tables.iteritems():
            for rel_name,rel_value in table_value.relations.iteritems():
                relations.append(rel_value)
        return relations                

    def checkrelations(self):
        for relation in self.relations:
            if relation.other not in self.tables.iterkeys():
                raise custom_exceptions.RelationError,\
                        "table %s does not exits" % relation.other
 
    def update_sa(self):
        try:
            for table in self.tables.itervalues():
                if hasattr(table,"sa_table"):
                    self.metadata.remove(table.sa_table)
                table.make_sa_table()
                table.make_sa_class()
            for table in self.tables.itervalues():
                table.sa_mapper()
        except (custom_exceptions.NoDatabaseError,\
                custom_exceptions.RelationError):
            pass

    def tables_with_relations(self,Table):
        self.checkrelations()
        relations = {}
        for n, v in Table.relations.iteritems():
            relations[v.other] = v
        for v in self.relations:
            if v.other == Table.name:
                relations[v.table.name] = v
        return relations

    def related_tables(self, Table):
        self.checkrelations()
        related_tables = {}
        for n, v in Table.relations.iteritems():
            related_tables[v.other] = v.type
        for v in self.relations:
            if v.other == Table.name:
                if v.type == 'manytoone':
                    relation = 'onetomany'
                elif v.type == 'onetomany':
                    relation = 'manytoone'
                elif v.type == 'onetoone':
                    relation = 'onetooneother'
                else:
                    relation = v.type
                related_tables[v.parent.table.name] = relation
        return related_tables


                        
            
            
    
            

            
            
            



