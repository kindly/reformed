from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

metadata = MetaData()
engine = create_engine('sqlite:///test4.db', echo = False)
metadata.bind = engine

# session
Session = sessionmaker(bind=engine, autoflush=True, transactional=True)
Session()

