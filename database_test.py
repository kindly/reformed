#!/usr/bin/env python
from fields import *
from tables import *
from database import *
from nose.tools import assert_raises,raises


class test_database(object):
     
    @classmethod
    def setUpClass(self):

        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.meta = sa.MetaData()
        self.Session = sa.orm.sessionmaker(bind =self.engine)
        self.Donkey = Database("Donkey",
                         Table("people",
                              Text("name"),
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
        assert len(self.Donkey.tables["people"].fields) == 3 # modified field
        assert len(self.Donkey.tables["email"].fields) == 2


    def test_relations(self):

        print self.Donkey.relations
        assert self.Donkey.relations[2].name == "Email" 

    def test_checkrelations(self):

        assert self.Donkey.checkrelations() is None

    def test_related_tables(self):

        
        assert self.Donkey.related_tables(self.Donkey.tables["people"])\
                                         ["email"] == "onetomany"
        assert self.Donkey.related_tables(self.Donkey.tables["email"])\
                                         ["people"] == "manytoone"


    def test_table_with_relations(self):

        d = self.Donkey

        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             ["email"].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             ["people"].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             ["email"].type == "onetomany"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             ["people"].type == "onetomany"

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

    def ttst_add_table_after_persist(self):

        self.Donkey.add_table(Table("New" , Text("new")))
        self.Donkey.persist()

        assert "New" in self.Donkey.tables

    @raises(custom_exceptions.NoTableAddError)
    def test_add_bad_table_after_persist(self):

        self.Donkey.add_table(Table("New2" , Text("new2"),
                              OneToMany("email","email")))

