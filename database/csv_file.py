import csv
import codecs
import datetime
import decimal
from StringIO import StringIO

## from python documentation
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        result = self.reader.readline().decode("utf-8")
        result = result.encode("utf-8")
        return result

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        self.line_num = self.reader.line_num
        if not row:
            raise StopIteration
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


def create_date_formats():
    """generate combinations of time and date formats with different delimeters"""

    date_formats = "dd/mm/yyyy mm/dd/yyyy yyyy/mm/dd".split()
    python_date_formats = "%d/%m/%Y  %m/%d/%Y %Y/%m/%d".split()
    both_date_formats = zip(date_formats, python_date_formats)

    #time_formats = "hh:mmz hh:mm:ssz hh:mmtzd hh:mm:sstzd".split()
    time_formats = "hh:mm:ssz hh:mm:sstzd".split()
    python_time_formats = "%H:%M%Z %H:%M:%S%Z %H:%M%z %H:%M:%S%z".split()
    both_time_fromats = zip(time_formats, python_time_formats)

    #date_seperators = ["-","."," ","","/","\\"]
    date_seperators = ["-",".",""]

    all_date_formats = []

    for seperator in date_seperators:
        for date_format, python_date_format in both_date_formats:
            all_date_formats.append(
                (
                 date_format.replace("/", seperator),
                 python_date_format.replace("/", seperator)
                )
            )

    all_formats = {}

    for date_format, python_date_format in all_date_formats:
        all_formats[date_format] = python_date_format
        for time_format, python_time_format in both_time_fromats:

            all_formats[date_format + time_format] = \
                    python_date_format + python_time_format

            all_formats[date_format + "T" + time_format] =\
                    python_date_format + "T" + python_time_format

            all_formats[date_format + " " + time_format] =\
                    python_date_format + " " + python_time_format
    return all_formats

DATE_FORMATS = create_date_formats()

POSSIBLE_TYPES = ["int", "bool", "decimal"] + DATE_FORMATS.keys()

class CsvFile(object):

    def __init__(self, path = None, headings = None,
                 format = None, skip_lines = 0,
                 buffer = None, types = None,
                 dialect = None, encoding = "utf-8"):

        self.path = path
        self.buffer = buffer
        self.defined_headings = headings
        self.types = types or {}
        self.file_headings = None
        self.skip_lines = skip_lines
        self.format = format
        self.headings_type = OrderedDict()
        self.headings = []
        self.dialect = dialect
        self.encoding = encoding

        self.guess_lines = 1000

    def get_dialect(self):

        if self.dialect:
            return

        if not self.format:
            try:
                if self.buffer:
                    flat_file = StringIO(self.buffer)
                else:
                    flat_file = open(self.path, mode = "rb")
                self.dialect = csv.Sniffer().sniff(flat_file.read(10240))
                if self.buffer:
                    flat_file.seek(0)
            finally:
                flat_file.close()
        else:
            if "quoting" in self.format:
                quoting = self.format["quoting"].upper()
                self.format["quoting"] = getattr(csv, quoting)
            class CustomDialect(csv.excel):
                pass
            for key, value in self.format.iteritems():
                setattr(CustomDialect, key, value)
            self.dialect = CustomDialect

    def get_headings(self):

        if self.defined_headings:
            return

        try:
            flat_file, csv_reader = self.get_csv_reader()

            self.file_headings = csv_reader.next()

        finally:
            flat_file.close()

    def parse_headings(self):

        headings = self.defined_headings or self.file_headings

        for heading in headings:
            try:
                name, type = heading.split("{")
                type = type.replace("}","")
            except ValueError:
                name, type = heading, None

            if type:
                self.check_type(type)

            self.headings_type[name] = type
            self.headings.append(name)

        self.add_extra_types()

    def add_extra_types(self):

        if not self.types:
            return
        for heading, type in self.types:
            if heading not in self.headings_type:
                continue
            self.headings_type[heading] = type


    def check_type(self, type):

        if type.lower() in  ("int", "integer",
                          "bool", "boolean",
                          "decimal", "string",
                          "varchar", "text"):
            return
        if type.lower() in DATE_FORMATS:
            return
        try:
            int(type)
        except ValueError:
            raise ValueError("date type %s not valid" % type)

    def guess_types(self):
        for num, name in enumerate(self.headings):
            type = self.headings_type[name]
            if not type:
                guessed_type = self.guess_type(num)
                if not guessed_type:
                    raise ValueError("unable to guess type for column %s"
                                     % name)
                self.headings_type[name] = guessed_type

    def is_int(self, val):

        try:
            int(val)
            return True
        except ValueError:
            return False

    def is_decimal(self, val):
        try:
            decimal.Decimal(val)
            return True
        except decimal.InvalidOperation:
            decimal.InvalidOperation
            return False

    def is_bool(self, val):
        if val.lower() in "1 true 0 false".split():
            return True
        return False

    def is_date_format(self, val, date_format):
        try:
            datetime.datetime.strptime(val, date_format)
            return True
        except ValueError:
            return False

    def check_possible_types(self, possible_types):

        if (len(possible_types) == 3 and
            "int" in possible_types and
            "decimal" in possible_types):
            possible_types.remove("int")
            possible_types.remove("decimal")
        if (len(possible_types) == 2 and
            "decimal" in possible_types):
            possible_types.remove("decimal")
        if 'bool' in possible_types:
            return 'bool'
        if len(possible_types) == 1:
            return possible_types.pop()

    def skip(self, csv_reader):

        if self.skip_lines:
            for num, line in enumerate(csv_reader):
                if num == self.skip_lines - 1:
                    return

    def guess_type(self, col):

        try:
            flat_file, csv_reader = self.get_csv_reader()

            if self.file_headings:
                csv_reader.next()

            possible_types = set(POSSIBLE_TYPES)

            max_length = 0

            for num, line in enumerate(csv_reader):
                if len(line) != len(self.headings):
                    continue
                value = line[col]
                max_length = max(max_length, len(value))
                if not value:
                    continue
                for type in list(possible_types):
                    if type == "int":
                        if not self.is_int(value):
                            possible_types.remove("int")
                    elif type == "bool":
                        if not self.is_bool(value):
                            possible_types.remove("bool")
                    elif type == "decimal":
                        if not self.is_decimal(value):
                            possible_types.remove("decimal")
                    else:
                        python_format = DATE_FORMATS[type]
                        if not self.is_date_format(value, python_format):
                            possible_types.remove(type)


                if num > self.guess_lines:
                    check = self.check_possible_types(possible_types)
                    if check:
                        return check

            if not possible_types:
                return min(max_length * 3, 2000)
            return self.check_possible_types(possible_types)

        finally:
            flat_file.close()

    def get_csv_reader(self):

        if self.buffer:
            flat_file = StringIO(self.buffer)
        else:
            flat_file = open(self.path, mode = "rb")

        csv_reader = UnicodeReader(flat_file, self.dialect, self.encoding)

        self.skip(csv_reader)

        return flat_file, csv_reader


    def chunk(self, lines):
        try:
            self.lines = lines
            flat_file, csv_reader = self.get_csv_reader()

            if self.file_headings:
                csv_reader.next()

            self.chunks = {}

            chunk = 0
            counter = 0
            total = 0
            offset = flat_file.tell()

            for num, line in enumerate(csv_reader):
                counter = counter + 1
                total = total + 1
                if counter == lines:
                    new_offset = flat_file.tell()
                    self.chunks[chunk] = (offset, new_offset)
                    offset = new_offset
                    counter = 0
                    chunk = chunk + 1
            new_offset = flat_file.tell()
            self.chunks[chunk] = (offset, new_offset)

            return total

        finally:
            if "flat_file" in locals():
                flat_file.close()

    def convert(self, line):

        new_line = []

        for num, value in enumerate(line):
            heading = self.headings[num]
            type = self.headings_type[heading]
            new_value = None

            if type == "int":
                new_value = int(value)
            elif type == "bool":
                new_value = bool(value)
            elif type == "decimal":
                new_value = decimal.Decimal(value)
            elif type in DATE_FORMATS:
                format = DATE_FORMATS[type]
                new_value = datetime.datetime.strptime(value, format)
            else:
                new_value = value

            new_line.append(new_value)

        return new_line

    def iterate_csv(self, chunk = None,
                    as_dict = False, convert = False,
                    no_end = False):

        try:
            flat_file, csv_reader = self.get_csv_reader()

            if self.file_headings:
                csv_reader.next()

            if chunk is not None:
                start, end = self.chunks[chunk]
            else:
                start, end = flat_file.tell(), None
            if no_end:
                end = None

            flat_file.seek(start)

            for line in csv_reader:
                if convert:
                    line = self.convert(line)
                if not as_dict:
                    stop = (yield line)
                else:
                    result = OrderedDict()
                    if len(line) != len(self.headings):
                        result["__error"] = "wrong length line"
                        result["original_line"] = line
                        stop = (yield result)
                    else:
                        for col_num, value in enumerate(line):
                            result[self.headings[col_num]] = value
                        stop = (yield result)
                if stop:
                    break
                if end and end <= flat_file.tell():
                    break

        finally:
            flat_file.close()

## {{{ http://code.activestate.com/recipes/576669/ (r18)
## Raymond Hettingers proporsal to go in 2.7
from collections import MutableMapping

class OrderedDict(dict, MutableMapping):

    # Methods with direct access to underlying attributes

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at 1 argument, got %d', len(args))
        if not hasattr(self, '_keys'):
            self._keys = []
        self.update(*args, **kwds)

    def clear(self):
        del self._keys[:]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            self._keys.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __iter__(self):
        return iter(self._keys)

    def __reversed__(self):
        return reversed(self._keys)

    def popitem(self):
        if not self:
            raise KeyError
        key = self._keys.pop()
        value = dict.pop(self, key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        inst_dict.pop('_keys', None)
        return (self.__class__, (items,), inst_dict)

    # Methods with indirect access via the above methods

    setdefault = MutableMapping.setdefault
    update = MutableMapping.update
    pop = MutableMapping.pop
    keys = MutableMapping.keys
    values = MutableMapping.values
    items = MutableMapping.items

    def __repr__(self):
        pairs = ', '.join(map('%r: %r'.__mod__, self.items()))
        return '%s({%s})' % (self.__class__.__name__, pairs)

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d
## end of http://code.activestate.com/recipes/576669/ }}}



if __name__ == "__main__":

    input = """a;b;c
1.5;afdfsaffsa;01012006
2.5;s;01012000
1;b;21012000
1;b;21012000
1;c;01012000"""

    csvfile = CsvFile("wee.txt", format = {"delimiter" : ";"})
    csvfile.get_dialect()
    csvfile.get_headings()
    csvfile.parse_headings()
    csvfile.guess_types()
    csvfile.chunk(1)

    #print "here"
    #for line in csvfile.iterate_csv():
    #    print line

    print "here"
    for line in csvfile.iterate_csv(0, convert = True, as_dict = True, no_end = True):
        print line





