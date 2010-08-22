import random
import re
import datetime
from sqlalchemy.exceptions import ProgrammingError
import sqlalchemy as sa
from formencode import Invalid


class MarkovText(object):

    def __init__(self):
        self.cache = {}

        self.parse_file('generator/alice.txt')

    def parse_file(self, file):
        """parse textfile and generate chains"""

        f = open(file)
        content = f.read()
        f.close()

        # assuming text is from Project Gutenberg
        # strip header/footer
        content = re.sub('(?ms)^.*\*\*\*\s*START\s[^\n]*\sPROJECT\s+GUTENBERG\s*EBOOK[^\n]*', '', content)
        content = re.sub('(?ms)\*\*\*\s*END\s[^\n]*\sPROJECT\s+GUTENBERG\s+EBOOK.*\Z', '', content)

        # split into words A, B, C, D
        # and add to cache
        # eg (A, B) = C, (B, C) = D
        words = content.split()
        for i in xrange(len(words)-2):
            w1, w2, w3 = words[i], words[i + 1], words[i + 2]
            key = (w1, w2)
            if key in self.cache:
                self.cache[key].append(w3)
            else:
                self.cache[key] = [w3]


    def text(self, length):
        """ Generate text up to length chars.  Whilst producing
        full sentances."""

        # Start after a full stop and when required length
        # exceeded cut to the previous one. This means that
        # text will be length or less chars

        # find word with full stop to start from
        w1 = ''
        while not w1.endswith('.'):
            (w1, w2) = random.choice(self.cache.keys())

        output = [w2]
        last_full_stop = 0
        current_length = len(w2)
        words = 1

        while True:
            w3 = random.choice(self.cache[(w1, w2)])
            output.append(w3)
            w1 = w2
            w2 = w3
            # length check
            current_length += len(w3) + 1
            if current_length >= length:
                break
            # sentance check
            words += 1
            if w3.endswith('.'):
                last_full_stop = words

        # trim to last full stop
        output = output[:last_full_stop]

        return ' '.join(output)




class DataGenerator(object):


    priority_generators = ['postcode', 'full_name']

    def __init__(self):
        self.word_lists = {}
        self.postcodes = {}
        # place to store table_lookup values
        self.table_lookups = {}

        self.images = {}
        self.textmaker = None
        self.curent_cache = {}
        self.random = 0

        # percentage of null data
        self.null_percent = 20
        # percentage of dirty data
        self.dirty_percent = 5

        self.generators = dict(
            # general generators
            Text = self.make_text,
            Integer = self.make_int,
            DateTime = self.make_date,
            Date = self.make_date,
            Email = self.make_email,
            Boolean = self.make_bool,
            TableLookup = self.make_table_lookup,
            Image = self.make_image,
            Thumb = self.make_image,
            # named generators
            full_name = self.make_name,
            postcode = self.make_postcode,
            town = self.make_town,
            road = self.make_road,
            dob = self.make_dob,
            sex = self.get_sex,
            phone = self.make_phone,
            core = self.make_core,
            lookup = self.make_lookup,
        )

        # text data_types
        self.text_data_types = ['Text', 'Email']


    def initialise(self, application):
        self.application = application
        if not self.word_lists:
            self.create_word_lists()
        if not self.postcodes:
            self.parse_postcodes()


    def create_word_lists(self):

        lists = ['last_names',
                 'first_names',
                 'boy_names',
                 'girl_names',
                 'verbs',
                 'nouns',
                 'adjectives',
                 'road_names']

        for list in lists:
            f = open('generator/%s' % list)
            self.word_lists[list] = f.read().split('\n')
            f.close()


    def new_record(self):

        # clear out the current cache
        self.curent_cache = {}

        # define a random value for the record
        # used for determening sex etc
        self.random = random.randint(0,99)


    def parse_postcodes(self):
        # read postcode file and create hash
        # of towns for the base code

        f = open('generator/postcodes')
        lines = f.read().split('\n')
        for line in lines:
            if line:
                (code, towns) = line.split('*')
                towns = towns.split('|')
                self.postcodes[code]=towns

    def is_male(self):

        if self.random < 50:
            return True
        else:
            return False

    def get_sex(self):

        if self.is_male():
            return 'Male'
        else:
            return 'Female'

    def make_phone(self):

        def number():
            number = self.make_char(min = 5, max = 8, chars= u'0123456789')
            if self.random % 11:
                mid = int(len(number)/2)
                number = u'%s %s' % (number[:mid], number[mid:])
            return number

        def code():
            return self.make_char(min = 1, max = 4, chars= u'0123456789')


        phone = u''
        if self.random % 5:
            # area code
            if self.random % 2:
                phone = u'0%s ' % code()
            else:
                phone = u'(%s) ' % code()

        return u'%s%s' % (phone, number())

    def make_town(self):
        """ return town use postcode if we know one """


        if not self.curent_cache.get('postcode'):
            # create a base postcode
            self.make_postcode()

        base = self.curent_cache.get('postcode')

        if self.postcodes.get(base[:2]):
            towns = self.postcodes.get(base[:2])
        else:
            towns = self.postcodes.get(base[:1])
        return random.choice(towns)


    def make_postcode(self):
        part1 = '%s%s' % (random.choice(self.postcodes.keys()), self.make_int(1,32))
        part2 = '%s%s' % (self.make_int(1,9), self.make_char(2,2,chars='ABCDEFGHJKLMNPRSTUVWXYZ'))
        postcode = "%s %s" % (part1, part2)
        # cache
        self.curent_cache['postcode'] = postcode
        return postcode


    def make_bool(self):
        options = [True, False]
        return random.choice(options)


    def make_list(self, list = 'nouns'):
        words = self.word_lists[list]
        out = random.choice(words)
        return out


    def make_road(self):
        return str(self.make_int(1,150)) + ' ' + self.make_word(1,2) + ' ' + self.make_list('road_names')

    def make_letter(self):
        return random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')

    def make_name(self):

        names = []
        self.curent_cache['name'] = []

        # first names
        num_names = random.triangular(0,4,1)
        initials = random.randint(0,99) < 10
        tail = (self.random % 2 == 0)

        for i in xrange(num_names):
            if initials:
                initial = self.make_letter()
                if tail:
                    initial += '.'
                names.append(initial)
            else:
                if self.is_male():
                    name = self.make_list('boy_names')
                else:
                    name = self.make_list('girl_names')

                names.append(name)
                self.curent_cache['name'].append(name)
                if random.randint(0,99) < 50:
                    initials = True

        # cache
        if random.randint(0,99) < 10:
            # double barrel
            p1 = self.make_list('last_names')
            p2 = self.make_list('last_names')
            self.curent_cache['name'].append(p1)
            self.curent_cache['name'].append(p2)
            names.append('%s-%s' % (p1, p2))
        else:
            name = self.make_list('last_names')
            self.curent_cache['name'].append(name)
            names.append(name)

        return ' '.join(names)
 

    def make_int(self, min = 0, max = 100):
        return random.randint(min,max)


    def make_date(self, min = 0, max = 0):
        """make date based on today offset by min/max in days"""

        # reverse min/max if needed
        if min > max:
            temp = min
            min = max
            max = temp
        delta = datetime.timedelta(random.randint(min, max))
        now = datetime.date.today()
        # iso format date
        return (now + delta).strftime('%Y-%m-%dT%H:%M:%SZ')


    def make_dob(self, min_age = 18, max_age = 80):
        # create date of birth
        dob = self.make_date(max_age * -365, min_age * -366)
        return dob


    def make_domain(self):
        # make a domain name
        tld = ['com', 'org', 'net', 'co.uk', 'org.uk', 'gov']
        out = self.make_word(1,2, delimit='.') + '.' + random.choice(tld)
        # only allow legal chars
        p = re.compile('[^a-zA-Z0-9.-]')
        out = p.sub('', out)
        return out


    def make_email(self):
        # do we have a name to base email on?
        bases = self.curent_cache.get('name')
        if bases:
            return random.choice(bases) + '@' + self.make_domain()
        else:
            return self.make_char(3,20, extras='__..') + '@' + self.make_domain()


    def make_word(self, min = 0, max = 10, delimit = ' '):
        out = []
        for i in xrange(random.randint(min, max)):
            x = random.randint(1,3)
            if x == 1:
                out.append(self.make_list('adjectives'))
            elif x == 2:
                out.append(self.make_list('nouns'))
            else:
                out.append(self.make_list('verbs'))
        out = delimit.join(out)
        return out


    def make_char(self, min = 0, max = 50, extras = '', chars= u'aabbcddeeeefghijklmnnoppqrssttuvwxyz'):
        chars = chars + extras
        out = u''
        for i in xrange(random.randint(min,max)):
            out += random.choice(chars)
        return out

    def make_random_chars(self, min = 0, max = 50):
        out = u''
        for i in xrange(random.randint(min, max)):
            out += chr(random.randint(32, 127))
        return out

    def make_core(self, type = 'people'):
        session = self.application.database.Session()
        obj = self.application.database.get_class('_core')
        result = session.query(obj.id).filter(obj.type == type).order_by(sa.func.random()).limit(1).first()
        id = result.id
        session.close()
        return id



    def make_table_lookup(self, table, field):
        name = '%s~%s' % (table, field)
        # check we have values if not fetch them
        if name not in self.table_lookups:
            self.make_lookup(table, field)
        # generate data
        data = self.table_lookups[name]
        out = None
        # if we have values select one
        if len(data):
            while not out:
                out = random.choice(data)
        return out


    def make_lookup(self, table, field):
        # get lookup values from a table
        # there is a limit on how many values are grabbed
        name = '%s~%s' % (table, field)
        self.table_lookups[name] = []
        data = self.table_lookups[name]
        rows = self.application.database.search(table, fields = [field], limit = 1000).data
        for row in rows:
            data.append(row[field])


    def make_image(self, category = ''):

        # sex type our immages
        if not category:
            if self.is_male():
                category = 'men'
            else:
                category = 'women'

        if category not in self.images:
            self.make_images(category)
        # generate data
        data = self.images[category]
        out = None
        # if we have values select one
        if len(data):
            while not out:
                out = random.choice(data)
        return out
 

    def make_images(self, category):
        # there is a limit on how many values are grabbed
        self.images[category] = []
        data = self.images[category]
        where = "mimetype = ?"
        values = ['image/jpeg']
        if category:
            where += " and category = ?"
            values.append(category)
        rows = self.application.database.search('upload', fields = ['id'], where = where, values = values, limit = 1000).data
        for row in rows:
            data.append(row['id'])


    def make_text(self, length = 250):
        if not self.textmaker:
            self.textmaker = MarkovText()
        return self.textmaker.text(random.randint(0, length))



    def create_generator_fields(self, table_name):
        """generate the field list for the table"""

        # clear the fields list
        self.fields = []
        table = self.application.database[table_name]
        if table.table_class:
            if table.table_class == 'communication':
                gen_info = dict(name = '_core_id', generator = 'core')
                gen_info['nullable'] = False
                gen_info['dirtyable'] = False
                self.fields.append(gen_info)

        for field in table.ordered_fields:
            if field.category <> "field":
                continue

            gen_info = dict(name = field.name)

            if field.generator:
                gen_info['generator'] = field.generator.get('name', field.type)
                if 'params' in field.generator:
                    gen_info['params'] = field.generator['params']
            else:
                gen_info['generator'] = field.type

            # are nulls allowed
            gen_info['nullable'] = field.nullable
            gen_info['field_type'] = field.type

            # FIXME field length not set correctly
            gen_info['length'] = field.length

            gen_info['dirtyable'] = (field.type in self.text_data_types)


            # check if this is a relationship based field
            try:
                relation_table = field.column.defined_relation.primary_key_table
                relation_column = field.column.original_clookupolumn
                gen_info['generator'] = 'TableLookup'
                gen_info['params'] = dict(table =  relation_table,
                                          field = relation_column)

            except AttributeError:
                pass

            # FIXME this wants to be moved
            if gen_info['generator'] in self.priority_generators:
                # high priority generators want to be created first
                self.fields.insert(0, gen_info)
            else:
                self.fields.append(gen_info)


    def generate_fields_for_obj(self, obj):

        for field in self.fields:
            gen = field['generator']
            try:
                params = field['params'].copy()
            except KeyError:
                params = {}

            # nulls
            if field['nullable']:
                if random.randint(0,99) < self.null_percent:
                    continue
            # ensure that value only set if gererated
            value = None
            # dirty
            if field['dirtyable'] and random.randint(0,99) < self.dirty_percent:
                # FIXME this line should not be needed
                length = field['length'] or 100
                value = self.make_random_chars(max = length)

            else:
                try:
                    if params:
                        value = self.generators[gen](**params)
                    else:
                        value = self.generators[gen]()


                except KeyError:
                    # no generator for this field
                    pass

            # set the value
            if value is not None:
                setattr(obj, field['name'], value)
                #print field['name'], value

class Generator(object):


    gen = DataGenerator()


    def __init__(self, application, **kw):

        self.kw = kw
        self.table = kw.get('table')
        try:
            self.number_requested = int(kw.get('number_requested'))
        except TypeError:
            self.number_requested = 0
        self.application = application

    def run(self, messager):

        self.gen.initialise(self.application)
        self.gen.create_generator_fields(self.table)

        commit_size = 50


        messager.message('starting', 0)

        r = self.application.database
        session = r.Session()
        records_needed = self.number_requested
        number_generated = 0


        while records_needed:
            if records_needed > commit_size:
                batch_size = commit_size
            else:
                batch_size = records_needed

            for i in xrange(batch_size):
                # starting new record so clear the generator
                self.gen.new_record()

                obj = r.get_instance(self.table)

                record = self.gen.generate_fields_for_obj(obj)

                try:
                    session.save(obj)
                except Invalid, e:
                    # cannot save due to validation error
                    # skip this attempt
                    batch_size -= 1
                    print 'RECORD fail', e

            session.commit()
            number_generated += batch_size
            records_needed -= batch_size
            messager.message('%s generated' % number_generated, (number_generated * 100)/self.number_requested)


        session.close()

        messager.message('finished', 100)






