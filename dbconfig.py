from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

metadata = MetaData()
engine = create_engine('sqlite:///donkey.sqlite', echo = False)
metadata.bind = engine
Session = sessionmaker(bind=engine, autoflush = False)

