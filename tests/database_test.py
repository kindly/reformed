#!/usr/bin/env python
from reformed.fields import *
from reformed.tables import *
from reformed.database import *
from nose.tools import assert_raises,raises
import logging

sqlhandler = logging.FileHandler("sql.log")
sqllogger = logging.getLogger('sqlalchemy.engine')
sqllogger.setLevel(logging.info)
sqllogger.addHandler(sqlhandler)


class test_database(object):
     
    @classmethod
    def setUpClass(self):

        self.engine = sa.create_engine('sqlite:///:memory:')
        self.meta = sa.MetaData()
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
                              )
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
        assert len(self.Donkey.tables["people"].fields) == 6 # modified field
        assert len(self.Donkey.tables["email"].fields) == 3


    def test_relations(self):

        print self.Donkey.relations
        assert "Email" in [email.name for email in self.Donkey.relations] 

    def test_checkrelations(self):

        assert self.Donkey.checkrelations() is None


    def test_table_with_relations(self):

        d = self.Donkey

        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             [("email","here")].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             [("people","other")].table.name == "people"
        assert d.tables_with_relations(self.Donkey.tables["people"])\
                                             [("email","here")].type == "onetomany"
        assert d.tables_with_relations(self.Donkey.tables["email"])\
                                             [("people","other")].type == "onetomany"

    def test_database_persist_tables(self):

        print self.Donkey.tables
        assert "__table" in self.Donkey.tables.keys()
        assert "__table_params" in self.Donkey.tables.keys()
        assert "__field" in self.Donkey.tables.keys()
        assert "__field_params" in self.Donkey.tables.keys()

    def test_database_persist_data(self):

        session = self.Session()
        all = session.query(self.Donkey.tables["__table_params"].sa_class).all()
        allfields = session.query(self.Donkey.tables["__field"].sa_class).all()
        allfield_param = session.query(self.Donkey.tables["__field_params"].sa_class).all()
           
        #assert (u"people",u"entity", u"True") in [(a.table_name, a.item,
        #                                           a.value) for a in all]
                                                    
        assert (u"people",u"name", u"Text") in [(a.table_name, a.field_name,
                                                   a.type) for a in allfields]

        assert (u"email",u"email", u"Text", None) in [(a.table_name, a.field_name,
                                                   a.type,
                                                   a.other) for a in allfields]

        assert (u"people",u"name2",u"length", u"10") in [(a.table_name, a.field_name, a.item,
                                                     a.value) for a in allfield_param]

    def test_add_table_after_persist(self):

        self.Donkey.add_table(Table("New" , Text("new")))
        self.Donkey.persist()

        assert "New" in self.Donkey.tables

    def test_persist_extra_field(self):

        self.Donkey.tables["people"].add_field(Text("name3", validation = "__^[a-zA-Z]*"))

        session = self.Donkey.Session()

        allfield_param = session.query(self.Donkey.tables["__field_params"].sa_class).all()

        assert (u"people",u"name3",u"validation", u"__^[a-zA-Z]*") in [(a.table_name, a.field_name, a.item,
                                                     a.value) for a in allfield_param]
        session.close()

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

    def test_boot_tables_persisted(self):

        assert u"__table" in [a.table_name for a in self.list_of_tables]
        assert u"__table_params" in [a.table_name for a in self.list_of_tables]
        assert u"__field" in [a.table_name for a in self.list_of_tables]

    def test_log_tables_persisted(self):
        assert (u"_log_people", u"name") in [(a.table_name,a.field_name) for a in self.list_of_fields]
        
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
        assert ("_core_entity", "donkey", "donkey" , "OneToOne") in [(a.table_name, a.field_name, a.other, a.type) for a in session.query(self.Donkey.get_class("__field")).all()]

