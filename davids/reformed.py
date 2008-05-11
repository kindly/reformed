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
                         sa.Column('field_param_type', sa.String(100), nullable = False, unique = True),
                         sa.Column('field_param_value', sa.String(100), nullable = False))

metadata.create_all(engine)

def attributesfromdict(d):
    self = d.pop('self')
    for n,v in d.iteritems():
        setattr(self,n,v)

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
    def __init__(self,name,field_param_type,field_param_value):
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
    
    def __init__(self, name, key,  *arg, **kw):
        
        attributesfromdict(locals())
        

class TextBox(object):
    
    def __init__(self,name,length =100, mandatory = True, *arg,**kw):
        
        attributesfromdict(locals())
    
    def Columns (self):
        
        return sa.Column(name,string(length), nullable = not mandatory)
    
class DropDown(object):
    
    


