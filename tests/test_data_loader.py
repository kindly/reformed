import donkey_test
from reformed.data_loader import *
from nose.tools import assert_raises,raises
from reformed.custom_exceptions import *
import formencode as fe
import yaml

class test_record_loader(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_record_loader).set_up_inserts()
        
        david ="""
        id : 1
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                email : poo@poo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            id : 1
            amount : 10
            _donkey : 
                name : fred
                age : 10
        """

        david = yaml.load(david)

        peter ="""
        name : peter
        address_line_1 : 16 blooey
        postcode : sewjfd
        email :
            -
                email : poo@poo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            amount : 10
            _donkey : 
                name : fred
                age : 10
        """

        peter = yaml.load(peter)

        people_table ="""
        table_name : people
        table_params :
            item : entity
            value : True
        field : 
            - 
                table_name : people
                field_name : email
                field_params :
                    item : cascade
                    value : all
            -
                table_name : people
                field_name : name
                field_params :
                    item : length
                    value : 50
        """

        existing_pk_record = yaml.load(people_table)

        email_order ="""
        table_name : people
        field_name : email
        item : order_by
        ___field :
            table_name : people
            field_name : email
        """

        existing_field_param = yaml.load(email_order)

        



        cls.session = cls.Donkey.Session()

        cls.existing_record = SingleRecord(cls.Donkey, "people", david)
        cls.new_record = SingleRecord(cls.Donkey, "people", peter)        
        cls.existing_pk = SingleRecord(cls.Donkey, "__table", existing_pk_record)
        cls.existing_field_param = SingleRecord(cls.Donkey, "__field_params", existing_field_param)

        cls.existing_pk.get_all_obj(cls.session)
        cls.new_record.get_all_obj(cls.session)
        cls.existing_record.get_all_obj(cls.session)
        cls.existing_field_param.get_all_obj(cls.session)
        #cls.new_record.load()

    
    def test_single_record_process(self):
        
        assert ("donkey_sponsership", 0, "_donkey", 0) in self.new_record.all_rows.keys()
        assert self.new_record.all_rows[("donkey_sponsership", 0, "_donkey", 0)] == dict(name = "fred", age =10) 
        assert self.new_record.all_rows[("email" , 1)] == dict(email = "poo2@poo.com")

    def test_get_key_data(self):

        assert get_key_data(("donkey_sponsership", 0, "_donkey", 0), self.Donkey , "people") == ["donkey", "manytoone", []]

        assert_raises(InvalidKey, get_key_data, 
                     ("donkey_sponsership", 0, "donkey", 0), self.Donkey , "people")

    def test_get_parent_key(self):

        assert_raises(InvalidKey, 
                      get_parent_key,
                      ("donkey_sponsership", 1, "donkey", 5),
                      self.new_record.all_rows)

        assert get_parent_key(("donkey_sponsership", 0, "donkey", 0),
                                             self.new_record.all_rows) == ("donkey_sponsership", 0)

        assert get_parent_key(("donkey", 0),
                                             self.new_record.all_rows) == "root" 

    def test_check_correct_fields(self):

        assert_raises(InvalidField, check_correct_fields, {"name":  "peter", "name2": "bob"}, self.Donkey, "people")

        assert check_correct_fields( {"name":  "peter", "postcode" : "bob"}, self.Donkey, "people") is None

        assert check_correct_fields( {"name":  "peter", "__options" : "bob"}, self.Donkey, "people") is None

        assert check_correct_fields( {"name":  "peter", "id" : "bob"}, self.Donkey, "people") is None

    def test_get_root_obj(self):

        assert self.new_record.all_obj["root"].id is None

        assert self.existing_record.all_obj["root"].name == u"david"

    def test_get_obj_with_id(self):

        obj = self.existing_record.get_obj_with_id( ("donkey_sponsership", 0) , dict(id = 1, amount = 20))

        assert obj.amount == 50   #originally 50

        assert_raises(InvalidData, self.existing_record.get_obj_with_id, ("donkey_sponsership", 0) , dict(id = 2, amount = 20))

        assert_raises(InvalidData, self.existing_record.get_obj_with_id, ("email", 0) , dict(id = 1))

    def test_get_obj_existing_one_to_many(self):

        assert self.existing_record.all_obj[("donkey_sponsership" , 0)].amount == 50

    def test_get_obj_new_one_to_many(self):

        assert self.existing_record.all_obj[("email" , 0)].email is None

    def test_get_obj_new_many_to_one(self):
        
        assert self.new_record.all_obj[("donkey_sponsership" , 0, "_donkey", 0)].age is None

    def test_get_obj_existing_many_to_one(self):
        
        assert self.existing_record.all_obj[("donkey_sponsership" , 0, "_donkey", 0)].age == 13

    def test_get_obj_existing_from_key(self):

        assert self.existing_pk.all_obj[("field", 0)].other == "email" 

        assert self.existing_pk.all_obj[("field", 1)].field_name == "name" 

    def test_get_obj_new_from_key(self):

        assert self.existing_pk.all_obj[("field", 1, "field_params", 0)].item  is None

    def test_get_existing_obj_from_key(self):

        assert self.existing_field_param.all_obj[("___field", 0)].field_name == "email"

    def test_key_parser(self):

        assert string_key_parser("poo") == ["poo"]
        assert string_key_parser("poo__24__weeee__2__plop") == ["poo", 24, "weeee", 2, "plop"]
        assert string_key_parser("___field__0__field_name") == ["___field", 0, "field_name"]
        
    def test_get_keys_and_items_from_list(self):

        assert get_keys_and_items_from_list(["poo__24__weeee__2__plop", "poo", "___field__0__field_name"]) ==\
                [[("poo", 24, "weeee", 2), "plop"],["root","poo"],[("___field", 0),"field_name"]]

    def test_get_keys_from_list(self):

        assert get_keys_from_list([[["poo", 24, "weeee", 2], "plop"],["root","poo"],[["___field", 0],"field_name"]])==\
                {"root":{}, ("poo", 24, "weeee", 2):{}, ("___field", 0):{}}
    
        
    def test_invalid(self):

        peter_invalid ="""
        name : peter
        email :
            -
                email : poopoo.com
            -
                email : poo2@poo.com
        donkey_sponsership:
            amount : a
            _donkey : 
                name : fred
                age : 90
        """

        peter_invalid = yaml.load(peter_invalid)

        invalid_record = SingleRecord(self.Donkey, "people", peter_invalid)

        assert_raises(fe.Invalid, invalid_record.load)

        try:
            invalid_record.load()
        except fe.Invalid, e:
            assert str(e) == """invalid object(s) are {'root': 'address_line_1: Please enter a value, postcode: Please enter a value', ('donkey_sponsership', 0): 'amount: Please enter a number', ('email', 0): 'email: An email address must contain a single @'}"""



    def test_z_add_values_to_obj(self):

        self.existing_record.add_all_values_to_obj()
        self.new_record.add_all_values_to_obj()
        self.existing_pk.add_all_values_to_obj()

        assert self.existing_record.all_obj[u"root"].address_line_1 == u"16 blooey"
        assert self.existing_record.all_obj[(u"donkey_sponsership" , 0)].amount == 10
        assert self.existing_record.all_obj[(u"email" , 0)].email == "poo@poo.com"

        assert self.new_record.all_obj[(u"root")].name == "peter"
        assert self.new_record.all_obj[(u"email" , 0)].email == "poo@poo.com"
        assert self.new_record.all_obj[(u"donkey_sponsership", 0,)].amount == 10
        assert self.new_record.all_obj[(u"donkey_sponsership", 0, "_donkey", 0)].age == 10
        
        assert self.existing_pk.all_obj[(u"table_params" , 0)].item == u"entity"
        assert self.existing_pk.all_obj[(u"table_params" , 0)].value == True

    def test_zz_load_record(self):

        self.new_record.load()

        people = self.session.query(self.Donkey.get_class(u"people")).all()
        email = self.session.query(self.Donkey.get_class(u"email")).all()
        donkey = self.session.query(self.Donkey.get_class(u"donkey")).all()
        donkey_spon = self.session.query(self.Donkey.get_class(u"donkey_sponsership")).all()
        

        assert (u"peter", u"sewjfd") in [( a.name, a.postcode) for a in 
                                         people]
        assert (u"fred", 10 ) in [( a.name, a.age) for a in 
                                         donkey]
        assert u"poo@poo.com" in [ a.email for a in 
                                         email]
        assert  10  in [ a.amount for a in 
                                         donkey_spon]


class test_flat_file(donkey_test.test_donkey):

    @classmethod
    def set_up_inserts(cls):

        super(cls, test_flat_file).set_up_inserts()

        cls.flatfile = FlatFile(cls.Donkey,
                            "people",
                            "tests/new_people.csv",    
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkey__0__name"]
                            )



    def test_parent_key(self):

        assert self.flatfile.make_parent_key_dict() == {('donkey_sponsership', 0, '_donkey', 0): ('donkey_sponsership', 0),
                                                   ('email', 1): 'root',
                                                   ('email', 0): 'root',
                                                   ('donkey_sponsership', 0): 'root'}

        assert_raises(custom_exceptions.InvalidKey, FlatFile, self.Donkey,
                                            "people",
                                            None,
                                            ["id",
                                            "name",
                                            "address_line_1",
                                            "postcode",
                                            "email__0__email",
                                            "email__1__email",
                                            "donkey_sponsership__0__amount",
                                            "donkey_sponsership__0__id",
                                            "donkey_sponsership__1___donkey__0__name"]
                                            )

    def test_get_key_info(self):

        assert self.flatfile.key_data == {('donkey_sponsership', 0, '_donkey', 0): ['donkey', 'manytoone', []],
                                                      ('email', 1): ['email', 'onetomany', []],
                                                      ('email', 0): ['email', 'onetomany', []],
                                                      ('donkey_sponsership', 0): ['donkey_sponsership', 'onetomany', []]}

        assert_raises(custom_exceptions.InvalidKey, FlatFile, self.Donkey,
                            "people",
                            None,
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkeyy__0__name"]
                            )

    def test_key_item_dict(self):

        assert self.flatfile.key_item_dict == {('donkey_sponsership', 0, '_donkey', 0): {'name': None},
                                               ('email', 1): {'email': None},
                                               'root': {'address_line_1': None, 'postcode': None, 'id': None, 'name': None},
                                               ('donkey_sponsership', 0): {'amount': None, 'id': None},
                                               ('email', 0): {'email': None}}

    def test_check_fields(self):

        assert self.flatfile.check_fields() == None

        assert_raises(custom_exceptions.InvalidField, FlatFile, self.Donkey,
                            "people",
                            None,
                            ["id",
                            "name",
                            "address_line_1",
                            "postcode",
                            "email__0__email",
                            "email__1__email",
                            "donkey_sponsership__0__amount",
                            "donkey_sponsership__0__id",
                            "donkey_sponsership__0___donkey__0__namee"]
                            )

    def test_get_descendants(self):

        assert self.flatfile.key_decendants == {('donkey_sponsership', 0, '_donkey', 0): [],
                                                ('email', 1): [],
                                                'root': [('donkey_sponsership', 0, '_donkey', 0), ('email', 1), ('donkey_sponsership', 0), ('email', 0)],
                                                ('email', 0): [],
                                                ('donkey_sponsership', 0): [('donkey_sponsership', 0, '_donkey', 0)]}

    def test_create_all_rows(self):

        assert self.flatfile.create_all_rows(["", "peter", "16 blooey", "sewjfd", "poo@poo.com", "poo2@poo.com", 10, None, "fred"]) ==\
                {('donkey_sponsership', 0, '_donkey', 0): {'name': 'fred'},
                 ('email', 1): {'email': 'poo2@poo.com'},
                 'root': {'postcode': 'sewjfd', 'name': 'peter', 'address_line_1': '16 blooey'},
                 ('email', 0): {'email': 'poo@poo.com'},
                 ('donkey_sponsership', 0): {'amount': 10}}

        assert self.flatfile.create_all_rows(["", "peter", "16 blooey", "sewjfd", "poo@poo.com", "poo2@poo.com", None, None, None]) ==\
                {('email', 1): {'email': 'poo2@poo.com'},
                 'root': {'postcode': 'sewjfd', 'name': 'peter', 'address_line_1': '16 blooey'},
                 ('email', 0): {'email': 'poo@poo.com'}}
        
        assert self.flatfile.create_all_rows(["", "peter", "16 blooey", "sewjfd", "poo@poo.com", "poo2@poo.com", None, None, "fred"]) ==\
                {('donkey_sponsership', 0, '_donkey', 0): {'name': 'fred'},
                 ('email', 1): {'email': 'poo2@poo.com'},
                 'root': {'postcode': 'sewjfd', 'name': 'peter', 'address_line_1': '16 blooey'},
                 ('email', 0): {'email': 'poo@poo.com'},
                 ('donkey_sponsership', 0): {}}

    def test_data_load(self):

        self.flatfile.load()

        result = self.session.query(self.Donkey.get_class("people")).filter_by(name = u"popp102").one()

        assert 102 in [a.amount for a in result.donkey_sponsership]

    def test_data_load_with_header(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/new_people_with_header.csv")    
        flatfile.load()


        result = self.session.query(self.Donkey.get_class("people")).filter_by(name = u"popph15").one()

        assert 1500 in [a.amount for a in result.donkey_sponsership]

    def test_data_load_with_header_error(self):

        flatfile = FlatFile(self.Donkey,
                            "people",
                            "tests/new_people_with_header_errors.csv")    

        
        print flatfile.load()
        assert flatfile.load() == [['name', 'address_line_1', 'postcode', 'email__0__email', 'email__1__email', 'donkey_sponsership__0__amount', 'donkey_sponsership__0___donkey__0__name', '__errors'], ['popph22', 'road22', 'post22', 'pop@pop.com', 'pop2@pop.com', 'poo', 'feddy2200', "{('donkey_sponsership', 0): Invalid('amount: Please enter a number',)}"], ['popph23', 'road23', 'post23', 'pop@pop.com', 'pop2@pop.com', '?', 'feddy2300', "{('donkey_sponsership', 0): Invalid('amount: Please enter a number',)}"], ['popph24', '', '', 'pop@pop.com', 'pop2@pop.com', '2400', 'feddy2400', "{'root': Invalid('address_line_1: Please enter a value\\npostcode: Please enter a value',)}"], ['popph27', '', '', 'pop@pop.com', 'pop2pop.com', '2700', 'feddy2700', "{('email', 1): Invalid('email: An email address must contain a single @',), 'root': Invalid('address_line_1: Please enter a value\\npostcode: Please enter a value',)}"], ['popph28', 'road28', 'post28', 'pop@pop.com', 'pop2pop.com', '2800', 'feddy2800', "{('email', 1): Invalid('email: An email address must contain a single @',)}"]]



