from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
import logging

logging.basicConfig(level=logging.DEBUG,
				filename='myapp.log',
				filemode='w')

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


metadata = MetaData()
engine = create_engine('sqlite:///test4.db', echo = False)
testengine = create_engine('sqlite:///:memory:', echo = False)
metadata.bind = engine

class ValidatedSession(Session):

	def save_or_update(self, instance, entity_name=None):
	
		if hasattr(instance,"validate"):
			if instance.validate():
				return instance.validate()
			else:
				super(ValidatedSession,self).save_or_update(instance, entity_name)
				return {}
		else:
			super(ValidatedSession,self).save_or_update(instance, entity_name)
			return {}

Session = sessionmaker(class_=ValidatedSession, bind=engine, autoflush=True, transactional=True)
SessionTest = sessionmaker(class_=ValidatedSession, bind=engine, autoflush=True, transactional=True)
Session()
SessionTest()
