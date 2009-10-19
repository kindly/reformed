import random



def make_int(min, max):
    return random.randint(min,max)

def make_char(min, max, extras = ''):
    chars = 'aabbcddeeeefghijklmnnoppqrssttuvwxyz' + extras
    out = ''
    for i in range(random.randint(min,max)):
        out += chars[random.randint(0,len(chars)-1)]
    return out

def make_domain():
    
    tld = ['com', 'org', 'net', 'co.uk', 'org.uk', 'gov']
    out = make_char(3, 10) + '.' + tld[random.randint(0,len(tld)-1)]
    return out

def make_email():
    return make_char(3,20, extras='__..') + '@' + make_domain()

num_rows = 100
filename = 'data.csv'
data = [
    ["name", make_char, (5, 10)],
    ["address_line_1", make_char, (5, 10)],
    ["postcode", make_char, (5, 10)],
    ["email__0__email" ,make_email, ()],
    ["email__1__email", make_email, ()],
    ["donkey_sponsership__0__amount", make_int, (1,50)],
    ["donkey_sponsership__0___donkey__0__name", make_char, (5, 10)],
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
    if i % 1000 == 0:
        print i
