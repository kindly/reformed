import sqlalchemy as sa
from sqlalchemy import orm
from session import *


class WidgetTemplate(object):
        
        
    def __init__(self, table):
            
        self.table = table

        if session.query(Widgets).filter(Widgets.name == table).filter(Widgets.widgetType == self.__class__.__name__).first() is None:
            session.save(Widgets(table,self.__class__.__name__))
            session.commit()
            self.table = table
        elif session.query(Widgets).filter(Widgets.name == table).filter(Widgets.widgetType <> self.__class__.__name__).first() is not None:
            raise "already have a widget named" + self.table
        
        try:
            self.createTables()
            self.createClasses()
            self.mapClasses()        
       
        except sa.exceptions.ArgumentError:
            print "already have a widget named " + self.table
        
       
        
    def __getattr__(self,name):
        return getattr(self, name + self.table)

    
class Dropdownbox3(WidgetTemplate):

    
    def createTables(self):
        self.terma_table = sa.Table(self.table+"terma", metadata,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column("terma", sa.types.String(100), nullable=False, unique= True)
            )

        self.termb_table = sa.Table(self.table+"termb", metadata,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('terma_id',sa.Integer, sa.ForeignKey(self.table+'terma.id')),
            sa.Column("termb", sa.types.String(100), nullable=False),
            sa.UniqueConstraint('termb', 'terma_id', name='uix_1')
            )

        self.termc_table = sa.Table(self.table+"termc", metadata,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('termb_id',sa.Integer, sa.ForeignKey(self.table+'termb.id')),
            sa.Column("termc", sa.types.String(100), nullable=False),
            sa.UniqueConstraint('termc', 'termb_id', name='uix_2')
            )
        
        self.dropdownValues = sa.Table(self.table+"Values", metadata,
                                       sa.Column('id', sa.Integer, primary_key=True),
                                       sa.Column('termc_id', sa.Integer, sa.ForeignKey(self.table+'termb.id')),
                                       sa.Column('form_id', sa.Integer, sa.ForeignKey(self.table+'termb.id')))
                                       
                                       

    def createClasses(self):

        def termainit (self, terma):
            self.terma = terma
        def termbinit (self, termb):
            self.termb = termb
        def termcinit (self, termc):
            self.termc = termc
        
        setattr(self,"Terma" + self.table, type("Terma" + self.table,(),{"__init__":termainit}))
        setattr(self,"Termb" + self.table, type("Termb" + self.table,(),{"__init__":termbinit}))
        setattr(self,"Termc" + self.table, type("Termc" + self.table,(),{"__init__":termcinit}))

        metadata.create_all(engine)
            

    def mapClasses(self):
        
                               
                    
        orm.mapper(self.Terma, self.terma_table, properties={
        'termb':orm.relation(self.Termb)
          })

        orm.mapper(self.Termb, self.termb_table ,properties={
        'termc':orm.relation(self.Termc)
          })

        orm.mapper(self.Termc, self.termc_table)


    def tableInsert(self,aa,bb,cc):
          
        if session.query(self.Terma).filter(self.Terma.terma == aa).first() is None:
            obja = self.Terma(aa)
            objb = self.Termb(bb)
            objc = self.Termc(cc)
            objb.termc.append(objc)
            obja.termb.append(objb)
            session.save(obja)
        elif session.query(self.Terma).filter(self.Terma.terma == aa).join("termb").filter(self.Termb.termb == bb).first() is None:
            obja = session.query(self.Terma).filter(self.Terma.terma == aa).one()
            objb = self.Termb(bb)
            objc = self.Termc(cc)
            objb.termc.append(objc)
            obja.termb.append(objb)
        elif session.query(self.Terma).filter(self.Terma.terma == aa).join("termb").filter(self.Termb.termb == bb).join(["termb","termc"]).filter(self.Termc.termc == cc).first() is None:
            obja = session.query(self.Terma).add_entity(self.Termb).filter(self.Terma.terma == aa).join("termb").filter(self.Termb.termb == bb).one()
            objb = obja[1]
            objc = self.Termc(cc)
            objb.termc.append(objc)


