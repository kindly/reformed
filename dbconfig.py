from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import SessionExtension

metadata = MetaData()
engine = create_engine('sqlite:///test4.db', echo = False)
metadata.bind = engine


Session = sessionmaker(bind=engine, autoflush=True, transactional=True)
Session()

