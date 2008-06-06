 #!/usr/bin/env python

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import sessionmaker


engine = sa.create_engine('sqlite:///:memory:', echo=True)

metadata = sa.MetaData()
Session = sessionmaker(bind=engine, autoflush=True, transactional=True)
session = Session()

tables = sa.Table("table", metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column("name", sa.types.String(100), nullable=False, unique= True)
                )

field  = sa.Table("field", metadata,
                sa.Column('id', sa.Integer, primary_key=True),
                sa.Column("name", sa.types.String(100), nullable=False),
                sa.Column("field_type", sa.types.String(100), nullable =False),
                sa.Column("table_id", sa.Integer, sa.ForeignKey("table.id")))

field_param = sa.Table("field_param", metadata,
                sa.Column( 'id' ,   sa.Integer,    primary_key=True),     
                sa.Column('field_id', sa.Integer, sa.ForeignKey("field.id")),
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
        return repr(self.__class__) + self.name
    
class Field(object):
    def __init__(self,name,field_type, field_param):
        attributesfromdict(locals())
    def __repr__(self):
        return repr(self.__class__) + self.name +self.field_type

class Field_param(object):
    def __init__(self,field_param_type,field_param_value):
        attributesfromdict(locals())
    def __repr__(self):
        return repr(self.__class__) +   self.field_param_type + self.field_param_value   
    
    
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
            columns.append(column.paramset(self.name))
        
        session.save(Tables(self.name,columns))
        session.commit()
    
    def create_table_def(self):
        
        columns = []
        
        for column in self.arg:
		if hasattr(column,"columns"):
            		columns.append(column.columns())
        
        self.table = sa.Table(self.name, metadata,
                              sa.Column('id' ,   sa.Integer,    primary_key=True),
                              *columns )
    
    def create_class(self):
        
        setattr(self, self.name,
        type(self.name, (object,), {"__init__": lambda self, **kw: attributesfromdictkw(locals())})
        )
        
    def create_mappings(self,database,table_name):
	
	prop = {}
        for column in self.arg:
		if hasattr(column,"parameters"):
			mapped_class = getattr(database.tbls[column.other], column.other) 
			prop[column.other]=column.parameters(table_name,mapped_class)

        orm.mapper(getattr(self, self.name), self.table, properties = prop)
    
    def add_external_columns(self,database, table_name):
	
        for column in self.arg:
		if hasattr(column,"external_column"):
			database.tbls[column.other].table.append_column( column.external_column(table_name))

    def add_external_tables(self,database, table_name):
	
        for column in self.arg:
		if hasattr(column,"external_table"):
			column.external_table(table_name)


class Integer(object):
   
    def __init__(self,name, mandatory = True, **kw):
        
        attributesfromdict(locals())

    def columns (self):
        
        return sa.Column(self.name,sa.Integer, nullable = not self.mandatory)
    
    def paramset (self,table_name):
        
        params = [Field_param(  "mandatory" , repr(self.mandatory)),]
        
        for n,v in self.kw.iteritems():
            params.append(Field_param(n,v))
               
        return Field(self.name,self.__class__.__name__,
                     params
                    )


class TextBox(object):
    
    def __init__(self,name,length =100, mandatory = True, **kw):
        
        attributesfromdict(locals())
    
    def columns (self):
        
        return sa.Column(self.name,sa.String(self.length), nullable = not self.mandatory)

    def paramset (self,table_name):
        
        params = [Field_param(  "length" , repr(self.length)),
                      Field_param(  "mandatory" , repr(self.mandatory))]
        
        for n,v in self.kw.iteritems():
            params.append(Field_param(n,v))
               
        return Field(self.name,self.__class__.__name__,
                     params
                    )


class OneToMany(object):
	
	def __init__(self,name,other, **kw):
		attributesfromdict(locals())
	
	def external_column (self,table_name):
		return  sa.Column(table_name+"_id", sa.Integer, sa.ForeignKey("%s.id"%(table_name)))
	
	def parameters (self, table_name, mapped_class):
		kw = self.kw
		return orm.relation(mapped_class,**kw) 
		


	def paramset (self,table_name):

		params = [Field_param(  "other" , self.other)]
		
		for n,v in self.kw.iteritems():
		    params.append(Field_param(n,v))
		       
		return Field(self.name,self.__class__.__name__,
			     params)

class ManyToMany(object):


	def __init__(self,name,other, **kw):
		attributesfromdict(locals())

	def external_table(self, table_name):

		self.table= sa.Table(table_name+"_manytomany_"+self.other, metadata,
				sa.Column(table_name+"_id", sa.Integer, sa.ForeignKey("%s.id"%(table_name))),
				sa.Column(self.other+"_id", sa.Integer, sa.ForeignKey("%s.id"%(self.other))))
		
	def parameters (self, table_name, mapped_class):
		kw = self.kw
		return orm.relation(mapped_class,secondary=self.table,**kw) 
	
	def paramset (self,table_name):

		params = [Field_param(  "other", self.other)]
		
		for n,v in self.kw.iteritems():
		    params.append(Field_param(n,v))
		       
		return Field(self.name,self.__class__.__name__,
			     params)


class Database(object):
	
    def __init__ (self):
        
        self.tbls = {}
        
        systables = session.query(Tables)
        
        for tab in systables:
            
            flds = []
            
            for fld in tab.field:
                
                params = {}
                
                for param in fld.field_param:
                    
			params[param.field_param_type.encode("ascii")] = param.field_param_value.encode("ascii")
            
                flds.append(globals()[fld.field_type.encode("ascii")](fld.name, **params))
            
	    self.tbls[tab.name.encode("ascii")] = Table(tab.name.encode("ascii"), *flds)
    
    def __getattr__(self, table):

	    return getattr(self.tbls[table],table)

    def create_tables(self):
        
        for v in self.tbls.itervalues():
            
            v.create_table_def()
	
	
	for v in self.tbls.itervalues():
            
            v.add_external_tables(self,v.name)
	 

        for v in self.tbls.itervalues():

            v.add_external_columns(self,v.name)

        metadata.create_all(engine)

        for v in self.tbls.itervalues():

            v.create_class()


        for v in self.tbls.itervalues():
            v.create_mappings( self,v.name)
            
      
if __name__ == "__main__":
    
    aa= Table("main_table",
		    TextBox("main_text_1"),
		    Integer("main_int"),
		    OneToMany("join_one_many","one_many", cascade='all,delete-orphan'),
		    ManyToMany("join_many_many","many_many"))
    bb= Table("one_many", TextBox("one_many_text_1"))
    cc= Table("many_many",TextBox("many_many_text_1"))

    aa.paramset()
    bb.paramset()
    cc.paramset()
   
  
    form = Table("form", TextBox("name"),
		    OneToMany("form_param","form_param"), OneToMany("form_item","form_item"))
    fromparam = Table("form_param", TextBox("key"), TextBox("value"))
    formitem = Table("form_item" ,TextBox("name") ,
		    TextBox("label"),TextBox("item"),
		    		    OneToMany("form_item_param","form_item_param"))

    formitemparam = Table("form_item_param", TextBox("key"),TextBox("value"))

    form.paramset()
    fromparam.paramset()
    formitem.paramset()
    formitemparam.paramset()
    
    data=Database()
    data.create_tables()

    nn = data.main_table(main_text_1="text1",main_int = 6,
		    one_many = [data.one_many( one_many_text_1= "one"),
	     		    data.one_many( one_many_text_1= "many")],
		    many_many = [data.many_many( many_many_text_1= "many"),
			   	data.many_many( many_many_text_1= "many")])

    session.save(nn)
    session.commit()
    
