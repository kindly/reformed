import sys
sys.path.append(".")
from .web.ajax import Worker, Sample, Generator
import random

if __name__ == "__main__":

    def bar(worker, environ):
        generator = worker.get_data_generator()
        environ['people_id'] = Sample('people', 'id', worker.application)
        environ['person'] = Generator(generator, ['full_name', 'Email', 'postcode', 'road', 'town'])


    def foo(worker, environ):
        new_id = environ['people_id']()
        worker.request_node("test.People", "edit", node_data = dict(id = new_id))
        
        data = worker.get_form_data('main')

        gen_data = environ['person']()
        data['name'] = gen_data.get('full_name')
        data['email'] = gen_data.get('Email')
        data['street'] = gen_data.get('road')
        data['town'] = gen_data.get('town')
        data['postcode'] = gen_data.get('postcode')

        node_data = worker.decode.get('node_data')
        form_data = [dict(form = 'main', data = data)]
        worker.request_node("test.People", "_save", node_data = node_data, form_data = form_data)
        offset = random.randint(1, 99)
        worker.request_node("test.People", "list", node_data = dict(l = 20, o = offset))


    a = Worker(application = 'testing',
               verbose = False,
               fake_server = True,
               profile = True,
               process = True,
               quiet = True)
    a.setup_function(bar)
    a.test_function(foo, count = 5)
    a.start()





