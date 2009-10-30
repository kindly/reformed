import random

l = ['last_names',
     'first_names',
     'verbs',
     'nouns',
     'adjectives',
     'road_names']

lists = {}

print 'make lists'
for list in l:
    f = open('generator/%s' % list)
    lists[list] = f.read().split('\n')
    f.close()
print 'lists made'

postcodes = {}
f = open('generator/postcodes')
lines = f.read().split('\n')
for line in lines:
    if line:
        (code, towns) = line.split('*')
        towns = towns.split('|')
        postcodes[code]=towns


def make_word(min, max, delimit = ' '):
    out = []
    for i in xrange(random.randint(min, max)):
        x = random.randint(1,3)
        if x == 1:
            out.append(make_list('adjectives'))
        elif x == 2:
            out.append(make_list('nouns'))
        else:
            out.append(make_list('verbs'))
    out = delimit.join(out)
    return out


def make_list(list):
    out = None
    while not out:
        out = lists[list][random.randint(0,len(lists[list])-1)]
    return out

def make_road():
    return str(make_int(1,150)) + ' ' + make_word(1,3) + ' ' + make_list('road_names')

def make_town(base = None):
    if base:
        base = current[base]
        if postcodes.get(base[:2]):
            towns = postcodes.get(base[:2])
        else:
            towns = postcodes.get(base[:1])
        return towns[random.randint(0, len(towns)-1)]
    else:
        return make_word(1,4)

def make_postcode():
    return postcodes.keys()[random.randint(0, len(postcodes)-1)] + str(make_int(1,32)) + ' ' + str(make_int(1,9)) + make_char(2,2,chars='ABCDEFGHJKLMNPRSTUVWXYZ')

def make_name():
    return make_list('first_names') + ' ' + make_list('last_names')

def make_int(min, max):
    return random.randint(min,max)

def make_char(min, max, extras = '', chars= u'aabbcddeeeefghijklmnnoppqrssttuvwxyz'):
    chars = chars + extras
    out = u''
    for i in xrange(random.randint(min,max)):
        out += chars[random.randint(0,len(chars)-1)]
    return out

def make_domain():

    tld = ['com', 'org', 'net', 'co.uk', 'org.uk', 'gov']
    out = make_word(1,2, delimit='.') + '.' + tld[random.randint(0,len(tld)-1)]
    return out

def make_email(base = None):
    if base:
        bases = current[base].split(' ')
        return bases[random.randint(0,len(bases)-1)] + '@' + make_domain()
    else:
        return make_char(3,20, extras='__..') + '@' + make_domain()

current = {}

def create_csv_from_data(filename, data, num_rows = 1000):

    f = open(filename,'w')


    header = ''
    for (title, fn, params) in data:
        header += '"%s", ' % title
    if header:
        header = header[:-2]
    f.write(header + '\n')
    global current
    for i in range(num_rows):
        row = u''
        current = {}
        for (title, fn, params) in data:
            value = fn(*(params))
            current[title] = value
            try:
                row += u'"%s", ' % value
            except:
                row += u'"ERROR", '
        if row:
            row = row[:-2]
        f.write(row + '\n')
        if (i + 1) % 1000 == 0:
            print "%s rows" % (i + 1)
    f.close()

    print "%s rows generated" % (i + 1)


def create_csv():
    full_data = [

   ( "data.csv", [
        ["name", make_name, ()],
        ["address_line_1", make_road, ()],
        ["postcode", make_postcode, ()],
        ["address_line_2", make_town, ('postcode', )],
        ["email__0__email" ,make_email, ('name', )],
        ["email__1__email", make_email, ('name', )],
        ["donkey_sponsership__0__amount", make_int, (1,50)],
        ["donkey_sponsership__0___donkey__0__name", make_word, (1,3)],
        ["donkey_sponsership__0___donkey__0__age", make_int, (1, 25)]
    ], 10000),
   ( "people.csv", [
        ["name", make_name, ()],
        ["address_line_1", make_road, ()],
        ["postcode", make_postcode, ()],
        ["address_line_2", make_town, ('postcode', )]
    ], 5000),
   ( "donkeys.csv", [
        ["name", make_word, (1,3)],
        ["age", make_int, (1, 25)]
    ], 20000)
    ]
 
    for (filename, data, num_rows) in full_data:
        create_csv_from_data(filename, data, num_rows)

