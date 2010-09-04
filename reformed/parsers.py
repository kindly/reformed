import pyparsing
from pyparsing import Word, nums, Regex, Optional
from dateutil.parser import parse

def get_result(parser, string, transform = lambda x:x):

    parsed = parser.scanString(string)

    result = None
    for item in parsed:
        result = item[0][0]
        search_term = result
        if result:
            break
    if result:
        return (result, transform(result))


def postcode(string):
    first_char = "".join(list(set(pyparsing.alphas)-set('QVXqvx')))
    second_char = "".join(list(set(pyparsing.alphas)-set('ijzIJZ')))
    third_char =  "ABCDEFGHJKSTUW" + "ABCDEFGHJKSTUW".lower()
    forth_char = "ABEHMNPRVWXY" + "ABEHMNPRVWXY".lower()
    fifth_char = "".join(list(set(pyparsing.alphas)-set('CIKMOVcikmov')))

    ending = pyparsing.Combine(Word(pyparsing.nums, exact=1) + Word(fifth_char, exact = 2))

    first_opt = pyparsing.Combine(Word(first_char, exact = 1) + Word(nums, exact = 1) )

    second_opt = pyparsing.Combine(Word(first_char, exact = 1) + Word(nums, exact = 2) )

    third_opt = pyparsing.Combine(Word(first_char, exact = 1) + Word(second_char, exact = 1) + Word(nums, exact = 1) )

    forth_opt = pyparsing.Combine(Word(first_char, exact = 1) + Word(second_char, exact = 1) + Word(nums, exact = 2) )

    fifth_opt = pyparsing.Combine(Word(first_char, exact = 1) + Word(nums, exact = 1) + Word(third_char, exact = 1) )

    sixth_opt = pyparsing.Combine(Word(first_char, exact = 1) + Word(second_char, exact = 1) + Word(nums, exact = 1) + Word(forth_char, exact = 1)) 

    def parse_post(string, pos, toks):
        return toks[0].upper() + " " + toks[1].upper()

    postcode =  ((second_opt + ending) |  (forth_opt + ending) | (first_opt + ending) | (third_opt + ending) | (fifth_opt + ending) | (sixth_opt + ending) |\
                (pyparsing.CaselessLiteral("GIR") + pyparsing.CaselessLiteral("0AA"))).setParseAction(parse_post)

    
    
    return get_result(postcode, string, lambda x:x.replace(" ",""))

def phonenumber(string):
    def parse_phone(string, pos, toks):

        parsed = "".join(toks)
        if len(parsed) < 6:
            parsed = ""
        return parsed

    phonenumber = pyparsing.OneOrMore(Word(nums, min = 3, max = 20)).setParseAction(parse_phone)

    return get_result(phonenumber, string)


def email(string):

    def parse_email(string, pos, toks):
        return string
    email = Regex(r"(?P<user>[A-Za-z0-9._%+-]+)@(?P<hostname>[A-Za-z0-9.-]+)\.(?P<domain>[A-Za-z]{2,4})")

    return get_result(email, string)


def date(string, dayfirst = True):
    iso_date_partial = Word(nums, exact =4) + "-" + Word(nums, exact =2) + "-" + Word(nums, exact = 2)

    iso_date_full = iso_date_partial + "T" + Word(nums, exact = 2)\
            + ":" + Word(nums, exact = 2) + ":" + Word(nums, exact = 2) + ("Z")

    regular_date = Word(nums, min=1, max=2) + "/" + Word(nums, min=1, max=2) + "/" + Word(nums, min =2, max=4)

    regular_date_hyphen = Word(nums, min=1, max=2) + "-" + Word(nums, min=1, max=2) + "-" + Word(nums, min =2, max=4)

    regular_date_dot = Word(nums, min=1, max=2) + "." + Word(nums, min=1, max=2) + "." + Word(nums, min =2, max=4)

    textual_date = (Word(nums, min=1, max=2) + Optional(",") + Optional(Word(pyparsing.alphas,  min=1, max=2)) + Optional(",")
                                            + Word(pyparsing.alphas, min=1, max=10) + Optional(",") + Word(nums, min =2, max=4))


    def parse_date(string, pos, toks):
        try:
            parse(string, dayfirst = dayfirst)
        except ValueError:
            return ""
        return parse(string, dayfirst = dayfirst)

    date = (iso_date_full | iso_date_partial | regular_date
            | regular_date_hyphen | regular_date_dot | textual_date).setParseAction(parse_date)

    return get_result(date, string)

if __name__ == "__main__":

    print postcode("se10qz") 
    print postcode("seqz") 
    print phonenumber("fsdfa@bob.com 74 3892743920") 
    print email("fsdfa@bob.com 74 3892743920") 
    print phonenumber("743 89") 
    print email("dave@wee.com") 
    print email("dave") 
    print date("1 jan 09") 
    print date("1.5.49") 
    print date("1.5.2009") 
    print date("n 09") 
    print date("1 jandfsaf 09") 








