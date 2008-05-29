from sqlalchemy import MetaData, create_engine

metadata = MetaData()
engine = create_engine('sqlite:///test.db', echo=False)
metadata.bind = engine



