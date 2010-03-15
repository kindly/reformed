#!/usr/bin/env python
from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import logging
import os

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)


class test_database(object):
     
    @classmethod
    def setUpClass(self):

        self.engine = sa.create_engine('sqlite:///:memory:')
        self.meta = sa.MetaData()

        try:
            os.remove("tests/zodb.fs")
            os.remove("tests/zodb.fs.lock")
            os.remove("tests/zodb.fs.index")
            os.remove("tests/zodb.fs.tmp")
        except OSError:
            pass
    
        self.Session = sa.orm.sessionmaker(bind =self.engine, autoflush = False)
        self.Donkey = Database("Donkey",
                         Table("people",
                              Text("name"),
                              Text("name2", length = 10),
                              OneToMany("Email","email"),
                              ),
                         Table("email",
                               Text("email")
                              ),
                               metadata = self.meta,
                               engine = self.engine,
                               session = self.Session,
                               zodb_store = "tests/zodb.fs",
                              )
        #self.Donkey.update_sa()
        self.Donkey.persist()

        self.session = self.Donkey.Session()

        #self.list_of_tables = self.session.query(self.Donkey.get_class("__table")).all()
    
        #self.list_of_fields = self.session.query(self.Donkey.get_class("__field")).all()
#   @classmethod
#   def tearDownClass(self):
#       del self.Donkey
#       del self.meta
#       del self.engine
#       del self.Session

    def test_basic(self):

        assert self.Donkey.name == "Donkey"
        assert "people" in self.Donkey.tables
        assert "email" in  self.Donkey.tables
        print self.Donkey.tables["people"].fields
        assert len(self.Donkey.tables["people"].fields) == 7 # modified field
        assert len(self.Donkey.tables["email"].fields) == 5


    def test_relations(self):

        print self.Donkey.relations
        assert "Email" in [email.name for email in self.Donkey.relations] 

    def test_checkrelations(self):

        assert self.Donkey.checkrelations() is None


    def test_table_with_relations(self):

        d = self.Donkey

        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             [("email","here")][0].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             [("people","other")][0].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             [("email","here")][0].type == "onetomany"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             [("people","other")][0].type == "onetomany"


    def test_add_table_after_persist(self):

        self.Donkey.add_table(Table("New" , Text("new")))
        self.Donkey.persist()

        assert "New" in self.Donkey.tables


    def test_add_field_after_persist(self):

        self.Donkey.tables["people"].add_field(Address("add"))

        session = self.Donkey.Session()

        newperson = self.Donkey.tables["people"].sa_class()
        newperson.address_line_1 = u"67 appplod street"
        newperson.postcode = u"sdffas"
        
        session.add(newperson)
        session.commit()

        new = session.query(self.Donkey.tables["people"].sa_class).all()

        assert (u"67 appplod street", "sdffas") in [(a.address_line_1,a.postcode) for a in new] 

        assert self.Donkey.validate_database() == [[],[],[],[],[]]
        
    @raises(custom_exceptions.NoTableAddError)
    def test_add_bad_table_after_persist(self):

        self.Donkey.add_table(Table("New2" , Text("new2"),
                              OneToMany("email","email")))
    
    def test_get_class(self):

        assert self.Donkey.get_class("people") is \
                self.Donkey.tables["people"].sa_class

        assert_raises(custom_exceptions.NoTableError,
                      self.Donkey.get_class,"peopley")
    
    def test_get_instance(self):

        assert isinstance(self.Donkey.get_instance("people"), 
                self.Donkey.tables["people"].sa_class)

        assert_raises(custom_exceptions.NoTableError,
                      self.Donkey.get_class,"peopley")

        
    def test_add_entity(self):

        assert_raises(custom_exceptions.NoTableAddError, self.Donkey.add_entity, 
                      Table("address2",
                            Address("address")
                                 ))

        self.Donkey.add_entity_table()

        self.Donkey.add_entity(Table("donkey", 
                               Text("name", validation = '__^[a-zA-Z0-9]*$'),
                               Integer("age", validation = 'Int')))

        self.Donkey.persist()

        assert "_core_entity" in self.Donkey.tables
        assert "donkey" in self.Donkey.tables
        assert self.Donkey.tables["donkey"].entity is True
        assert self.Donkey.tables["donkey"].kw["entity"] is True
        session = self.Donkey.Session()
        #assert ("_core_entity", "donkey", "donkey" , "OneToOne") in [(a.table_name, a.field_name, a.other, a.type) for a in session.query(self.Donkey.get_class("__field")).all()]

