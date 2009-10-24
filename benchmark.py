import reformed.reformed as r
import data_creator as d
import datetime

data = []

fields = [
    ["name", d.make_char, (5, 10)],
    ["address_line_1", d.make_char, (5, 10)],
    ["postcode", d.make_char, (5, 10)]
    ]

table = 'people'

num_rows = 1000
for i in range(num_rows):
    row = []
    for j in range(len(fields)):
        row.append(fields[j][1](*fields[j][2]))
    data.append(row)

print 'generated'

print 'commit every line and core entity table being made'

start = datetime.datetime.now()

session = r.reformed.Session()
for i in range(num_rows):
    obj = r.reformed.get_instance(table)
    for j in range(len(fields)):
        setattr(obj, fields[j][0], data[i][j])
    session.save_or_update(obj)
    session.commit()
    if i and i % 100 == 0:
        print i

time = (datetime.datetime.now() - start).seconds
try:
    rate = num_rows/time
except:
    rate = 'n/a'

print 'finished\ntime %s seconds  rate %s rows/s' % (time, rate)

print 'fastest with core entity being made'
start = datetime.datetime.now()

session = r.reformed.Session()
for i in range(num_rows):
    obj = r.reformed.get_instance(table)
    for j in range(len(fields)):
        setattr(obj, fields[j][0], data[i][j])
    session.add(obj)
    if i and i % 250 == 0:
        session.commit()
        print i

time = (datetime.datetime.now() - start).seconds
try:
    rate = num_rows/time
except:
    rate = 'n/a'

print 'finished\ntime %s seconds  rate %s rows/s' % (time, rate)

print 'fastest sqlalchemy no relationships'
start = datetime.datetime.now()

session = r.reformed.Session()
for i in range(num_rows):
    obj = r.reformed.get_instance(table)
    for j in range(len(fields)):
        setattr(obj, fields[j][0], data[i][j])
        setattr(obj, "_core_entity_id", 1)
    session.session.add(obj)

session.session.commit()

time = (datetime.datetime.now() - start).seconds
try:
    rate = num_rows/time
except:
    rate = 'n/a'

print 'finished\ntime %s seconds  rate %s rows/s' % (time, rate)
