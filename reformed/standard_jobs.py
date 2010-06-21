from search import Search
from datetime import datetime, timedelta
import time
import util
from data_loader import FlatFile
from sqlalchemy.exceptions import ConcurrentModificationError, ProgrammingError

class Messager(object):

    def __init__(self, application, job_id):
        self.application = application
        self.database = application.database
        self.job_id = job_id

    def message(self, message, percent = None):

        row = self.database.search_single_data("_core_job_scheduler", "id = %s" % self.job_id, internal = True)

        row["message"] = u"%s" % message

        if percent:
            row["percent"] = percent

        # FIXME don't like this here
        try:
            util.load_local_data(self.database, row)
        except ConcurrentModificationError:
            pass



def data_load_from_file(application, job_id, **kw):

    table = kw.get("table")
    file = kw.get("file")

    flatfile = FlatFile(application.database,
                        table,
                        util.get_dir(file))

    messager = Messager(application, job_id)

    return flatfile.load(messager = messager)


def wait(application, job_id, **kw):

    number = kw.get("time")

    time.sleep(int(number))
    return "%s is done!" % number

def error(application, job_id, **kw):
    number = kw.get("time")
    assert 1 <> 1


def generate(application, job_id, **kw):

    generator = Generater(application, **kw)

    messager = Messager(application, job_id)

    return generator.run(messager = messager)


import data_creator




class Generater(object):

    priority_generators = ['postcode']

    generators = dict(
        # general generators
        Text = data_creator.make_word,
        Integer = data_creator.make_int,
        Boolean = data_creator.make_bool,
        # named generators
        full_name = data_creator.make_name,
        postcode = data_creator.make_postcode,
        town = data_creator.make_town,
        road = data_creator.make_road,
        dob = data_creator.make_dob,
    )

    def __init__(self, application, **kw):

        self.kw = kw
        self.table = kw.get('table')
        try:
            self.number_requested = int(kw.get('number_requested'))
        except TypeError:
            self.number_requested = 0
        self.application = application

    def run(self, messager):
        print 'generating...'
        commit_size = 50

        fields = self.create_generator_fields(self.table)

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
                obj = r.get_instance(self.table)
                postcode = None
                for field in fields:
                    gen = field['generator']
                    try:
                        params = field['params'].copy()
                    except KeyError:
                        params = {}

                    # towns are based on postcodes
                    if gen == 'town' and postcode:
                        params['base'] = postcode
                    try:
                        if params:
                            value = self.generators[gen](**params)
                        else:
                            value = self.generators[gen]()

                        # cache any special 'reusable' values
                        if gen == 'postcode':
                            postcode = value
                        # set the value
                        setattr(obj, field['name'], value)
                    except KeyError:
                        # no generator for this field
                        pass

                session.save(obj)

            try:
                session.commit()
                number_generated += batch_size
                records_needed -= batch_size
                messager.message('%s generated' % number_generated, (number_generated * 100)/self.number_requested)
            except ProgrammingError:
                # FIXME we are getting funny unicode error due to
                # town names with none ascii names
                print 'GGGRR we are struck by the evil unicode error'
                session.rollback()
                pass

        session.close()

        messager.message('finished', 100)
        return 'complete %s records created' % self.number_requested


    def create_generator_fields(self, table_name):

        fields = []
        table = self.application.database[table_name]
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
            try:
                print field.name, field.relations, gen_info['generator'], field.foreign_key_name
            except:
                pass
            if gen_info['generator'] in self.priority_generators:
                # high priority generators want to be created first
                fields.insert(0, gen_info)
            else:
                fields.append(gen_info)

        return fields



