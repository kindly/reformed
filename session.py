#!/usr/bin/env python
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import sessionmaker



engine = sa.create_engine('sqlite:///C:/Python25/widget start/wid.db', echo=True)
metadata = sa.MetaData()
Session = sessionmaker(bind=engine, autoflush=True, transactional=True)
session = Session()



widgets_table = sa.Table("widgets", metadata,
                         sa.Column('id', sa.Integer, primary_key=True),
                         sa.Column("name", sa.types.String(100), nullable=False, unique= True),
                         sa.Column("widgetType", sa.types.String(100), nullable=False))




formType_table = sa.Table("formType", metadata,
                         sa.Column('id', sa.Integer, primary_key=True),
                         sa.Column("name", sa.types.String(100), nullable=False, unique= True),
                         sa.Column("formType", sa.types.String(100), nullable=False)
                         )




metadata.create_all(engine)            

class Widgets(object):
    def __init__(self,name,widgetType):
            self.name =name
            self.widgetType =widgetType

orm.mapper(Widgets, widgets_table)
