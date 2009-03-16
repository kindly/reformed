#!/usr/bin/env python
from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises


class test_database(object):
     
    @classmethod
    def setUpClass(self):

        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.meta = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine, autoflush = False)
        self.Donkey = Database("Donkey",
                         Table("people",
                              Text("name"),
                              Text("name2", length = 10),
                              OneToMany("Email","email"),
                              entity = True),
                         Table("email",
                               Text("email")
                              ),
                               metadata = self.meta,
                               engine = self.engine,
                               session = self.Session)
        #self.Donkey.update_sa()
        self.Donkey.persist()

        self.session = self.Donkey.Session()

        self.list_of_tables = self.session.query(self.Donkey.get_class("__table")).all()
    
        self.list_of_fields = self.session.query(self.Donkey.get_class("__field")).all()
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
        assert len(self.Donkey.tables["people"].fields) == 4 # modified field
        assert len(self.Donkey.tables["email"].fields) == 2


    def test_relations(self):

        print self.Donkey.relations
        assert self.Donkey.relations[2].name == "Email" 

    def test_checkrelations(self):

        assert self.Donkey.checkrelations() is None


    def test_table_with_relations(self):

        d = self.Donkey

        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             [("email","this")].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             [("people","other")].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             [("email","this")].type == "onetomany"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             [("people","other")].type == "onetomany"

    def test_database_persist_tables(self):

        print self.Donkey.tables
        assert "__table" in self.Donkey.tables.keys()
        assert "__table_params" in self.Donkey.tables.keys()
        assert "__field" in self.Donkey.tables.keys()

    def test_database_persist_data(self):

        session = self.Session()
        all = session.query(self.Donkey.tables["__table_params"].sa_class).all()
        allfields = session.query(self.Donkey.tables["__field"].sa_class).all()
           
        assert (u"people",u"entity", u"True") in [(a.table_name, a.item,
                                                   a.value) for a in all]
                                                    
        assert (u"people",u"name", u"Text") in [(a.table_name, a.name,
                                                   a.type) for a in allfields]

        assert (u"email",u"email", u"Text", None) in [(a.table_name, a.name,
                                                   a.type,
                                                   a.other) for a in allfields]

    def test_add_table_after_persist(self):

        self.Donkey.add_table(Table("New" , Text("new")))
        self.Donkey.persist()

        assert "New" in self.Donkey.tables

    @raises(custom_exceptions.NoTableAddError)
    def test_add_bad_table_after_persist(self):

        self.Donkey.add_table(Table("New2" , Text("new2"),
                              OneToMany("email","email")))
    
    def test_get_class(self):

            assert self.Donkey.get_class("people") is \
                    self.Donkey.tables["people"].sa_class

            assert_raises(custom_exceptions.NoTableError,
                          self.Donkey.get_class,"peopley")
    
    def test_get_class(self):

            assert isinstance(self.Donkey.get_instance("people"), 
                    self.Donkey.tables["people"].sa_class)

            assert_raises(custom_exceptions.NoTableError,
                          self.Donkey.get_class,"peopley")

    def test_boot_tables_persisted(self):

        assert u"__table" in [a.table_name for a in self.list_of_tables]
        assert u"__table_params" in [a.table_name for a in self.list_of_tables]
        assert u"__field" in [a.table_name for a in self.list_of_tables]

    def test_log_tables_persisted(self):
        assert (u"_log_people", u"name") in [(a.table_name,a.name) for a in self.list_of_fields]
        
