 #!/usr/bin/env python

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import sessionmaker


engine = sa.create_engine('sqlite:///:memory:', echo=True)
metadata = sa.MetaData()
Session = sessionmaker(bind=engine, autoflush=True, transactional=True)
session = Session()

tables = sa.Table("table", metadata,
                sa.Column('table_id', sa.Integer, primary_key=True),
                sa.Column("name", sa.types.String(100), nullable=False, unique= True)
                )

field  = sa.Table("field", metadata,
                sa.Column('field_id', sa.Integer, primary_key=True),
                sa.Column("name", sa.types.String(100), nullable=False, unique= True),
                sa.Column("field_type", sa.types.String(100), nullable =False),
                sa.Column("tableid", sa.Integer, sa.ForeignKey("table.table_id")))

field_param = sa.Table("field_param", metadata,
                sa.Column( 'field_param_id' ,   sa.Integer,    primary_key=True),     
                sa.Column('field_id', sa.Integer, sa.ForeignKey("field.field_id")),
                sa.Column('field_param_type', sa.String(100), nullable = False),
                sa.Column('field_param_value', sa.String(100), nullable = False))

metadata.create_all(engine)

def attributesfromdict(d):
    self = d.pop('self')
    for n,v in d.iteritems():
        setattr(self,n,v)
        
def attributesfromdictkw(d):
    self = d.pop('self')
    kw = d.pop('kw')
    for n,v in d.iteritems():
        setattr(self,n,v)
    for p,q in kw.iteritems():
        setattr(self,p,q)        

class Tables(object):
    def __init__(self,name, field):
        attributesfromdict(locals())
    def __repr__(self):
        return repr(self.__class__) +  repr(self.__dict__)
    
class Field(object):
    def __init__(self,name,field_type, field_param):
        attributesfromdict(locals())
    def __repr__(self):
        return repr(self.__class__) +  repr(self.__dict__)

class Field_param(object):
    def __init__(self,field_param_type,field_param_value):
        attributesfromdict(locals())
    def __repr__(self):
        return repr(self.__class__) +  repr(self.__dict__)    
    
    
orm.mapper(Tables, tables, properties={
        'field':orm.relation(Field)
          })

orm.mapper(Field, field, properties={
        'field_param':orm.relation(Field_param)
          })

orm.mapper(Field_param,field_param)


class Table(object):
    
    def __init__(self, name, *arg, **kw):
        
        attributesfromdict(locals())  ## args need instance checking
        
    def paramset(self):
        
        columns = []
        
        for column in self.arg:
            columns.append(column.paramset())
        
        session.save(Tables(self.name,columns))
        session.commit()
    
    def create_table_def(self):
        
        columns = []
        
        for column in self.arg:
            columns.append(column.columns())
        
        self.table = sa.Table(self.name, metadata,
                              sa.Column( self.name + '_id' ,   sa.Integer,    primary_key=True),
                              *columns )
    
    def create_class(self):
        
        setattr(self, self.name,
        type(self.name, (object,), {"__init__": lambda self, **kw: attributesfromdictkw(locals())})
        )
        
    def create_mappings(self):
        orm.mapper(getattr(self, self.name), self.table)
    
    def create_table(self):
        self.create_table_def()
        self.create_class()
        self.create_mappings()
        

class TextBox(object):
    
    def __init__(self,name,length =100, mandatory = True, **kw):
        
        attributesfromdict(locals())
    
    def columns (self):
        
        return sa.Column(self.name,sa.String(self.length), nullable = not self.mandatory)
    
    def paramset (self):
        
        params = [Field_param(  "length" , self.length),
                      Field_param(  "mandatory" , repr(self.mandatory))]
        
        for n,v in self.kw.iteritems():
            params.append(Field_param(n,repr(v)))
               
        return Field(self.name,self.__class__.__name__,
                     params
                    )


class Database(object):
    
    def __init__ (self):
        
        self.tbls = {}
        
        systables = session.query(Tables)
        
        for tab in systables:
            
            flds = []
            
            for fld in tab.field:
                
                params = {}
                
                for param in fld.field_param:
                    
                    params[param.field_param_type] = param.field_param_value
            
                flds.append(globals()[fld.field_type](fld.name, **params))
            
##          setattr(self, tab.name, Table(str(tab.name), *flds))
            
            self.tbls[tab.name] = Table(str(tab.name), *flds)
    
    def create_tables(self):
        
        for v in self.tbls.itervalues():
            
            v.create_table()
        
        metadata.create_all(engine)
        
            


    
    
    
    
    
if __name__ == "__main__":
    
    aa= Table("aa", TextBox("bb"), TextBox("cc"))
    bb= Table("dd", TextBox("ee"), TextBox("ff"))
    aa.paramset()
    bb.paramset()
    data=Database()
    
    
