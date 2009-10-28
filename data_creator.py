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


def make_word(min, max):
    out = []
    for i in xrange(random.randint(min, max)):
        x = random.randint(1,3)
        if x == 1:
            out.append(make_list('adjectives'))
        elif x == 2:
            out.append(make_list('nouns'))
        else:
            out.append(make_list('verbs'))
    out = " ".join(out)
    return out


def make_list(list):
    return lists[list][random.randint(0,len(lists[list])-1)]

def make_road():
    return str(make_int(1,150)) + ' ' + make_word(1,3) + ' ' + make_list('road_names')

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
    out = make_char(3, 10) + '.' + tld[random.randint(0,len(tld)-1)]
    return out

def make_email():
    return make_char(3,20, extras='__..') + '@' + make_domain()


def create_csv():
    num_rows = 5000
    filename = 'data.csv'
    data = [
        ["name", make_name, ()],
        ["address_line_1", make_road, ()],
        ["postcode", make_postcode, ()],
        ["email__0__email" ,make_email, ()],
        ["email__1__email", make_email, ()],
        ["donkey_sponsership__0__amount", make_int, (1,50)],
        ["donkey_sponsership__0___donkey__0__name", make_word, (1,3)],
        ["donkey_sponsership__0___donkey__0__age", make_int, (1, 25)]
    ]

    f = open(filename,'w')


    header = ''
    for (title, fn, params) in data:
        header += '"%s", ' % title
    if header:
        header = header[:-2]
    f.write(header + '\n')

    for i in range(num_rows):
        row = ''
        for (title, fn, params) in data:
             row += '"%s", ' % fn(*params)
        if row:
            row = row[:-2]
        f.write(row + '\n')
        if (i + 1) % 1000 == 0:
            print "%s rows" % (i + 1)
    f.close()

    print "%s rows generated" % (i + 1)
