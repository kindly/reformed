# -*- coding: latin-1 -*-
"""selector - WSGI delegation based on URL path and method.

(See the docstring of selector.Selector.)

Copyright (C) 2006 Luke Arno - http://lukearno.com/

This program is free software; you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by the 
Free Software Foundation; either version 2 of the License, or (at your 
option) any later version.

This program is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to:

The Free Software Foundation, Inc., 
51 Franklin Street, Fifth Floor, 
Boston, MA  02110-1301, USA.

Luke Arno can be found at http://lukearno.com/

adapted (some stuff removed) for reformed
"""

import re


class MappingFileError(Exception): pass


class PathExpressionParserError(Exception): pass


def method_not_allowed(environ, start_response):
    """Respond with a 405 and appropriate Allow header."""
    start_response("405 Method Not Allowed", 
                   [('Allow', ', '.join(environ['selector.methods'])),
                    ('Content-Type', 'text/plain')])
    return ["405 Method Not Allowed\n\n"
            "The method specified in the Request-Line is not allowed "
            "for the resource identified by the Request-URI."] 


def not_found(environ, start_response):
    """Respond with a 404."""
    start_response("404 Not Found", [('Content-Type', 'text/plain')])
    return ["404 Not Found\n\n"
            "The server has not found anything matching the Request-URI."]


class Selector(object):
    """WSGI middleware for URL paths and HTTP method based delegation.
    
    see http://lukearno.com/projects/selector/

    mappings are given are an iterable that returns tuples like this:

    (path_expression, http_methods_dict, optional_prefix)
    """
    
    status405 = staticmethod(method_not_allowed)
    status404 = staticmethod(not_found)
    
    def __init__(self, mappings=None, prefix="", parser=None, wrap=None, mapfile=None):
        """Initialize selector."""
        self.mappings = []
        self.prefix = prefix
        if parser is None:
            self.parser = SimpleParser()
        else:
            self.parser = parser
        self.wrap = wrap
        if mapfile is not None:
            self.slurp_file(mapfile)
        if mappings is not None: 
            self.slurp(mappings)

    def slurp(self, mappings, prefix=None, parser=None, wrap=None):
        """Slurp in a whole list (or iterable) of mappings.
        
        Prefix and parser args will override self.parser and self.args
        for the given mappings.
        """
        if prefix is not None:
            oldprefix = self.prefix
            self.prefix = prefix
        if parser is not None:
            oldparser = self.parser
            self.parser = parser
        if wrap is not None:
            oldwrap = self.wrap
            self.wrap = wrap
        list(starmap(self.add, mappings))
        if wrap is not None:
            self.wrap = oldwrap
        if parser is not None:
            self.parser = oldparser
        if prefix is not None:
            self.prefix = oldprefix

    def add(self, path, method_dict=None, prefix=None, **http_methods):
        """Add a mapping.
        
        HTTP methods can be specified in a dict or using kwargs,
        but kwargs will override if both are given.
        
        Prefix will override self.prefix for this mapping.
        """
        # Thanks to Sébastien Pierre 
        # for suggesting that this accept keyword args.
        if method_dict is None:
            method_dict = {}
        if prefix is None:
            prefix = self.prefix
        method_dict = dict(method_dict)
        method_dict.update(http_methods)
        if self.wrap is not None:
            for meth, cbl in method_dict.items():
                method_dict[meth] = self.wrap(cbl)
        regex = self.parser(self.prefix + path)
        compiled_regex = re.compile(regex)
        self.mappings.append((compiled_regex, method_dict))

    
    def __call__(self, environ, start_response):
        """Delegate request to the appropriate WSGI app."""
        app, environ['selector.vars'], environ['selector.methods'] = \
            self.select(environ['PATH_INFO'], environ['REQUEST_METHOD'])
        return app(environ, start_response)

    
    def select(self, path, method):
        """Figure out which app to delegate to or send 404 or 405."""
        for regex, method_dict in self.mappings:
            match = regex.search(path)
            if match:
                methods = method_dict.keys()
                if method_dict.has_key(method):
                    return method_dict[method], match.groupdict(), methods
                elif method_dict.has_key('_ANY_'):
                    return method_dict['_ANY_'], match.groupdict(), methods
                else:
                    return self.status405, {}, methods
        return self.status404, {}, []




class SimpleParser(object):
    """Callable to turn path expressions into regexes with named groups.
    
    For instance "/hello/{name}" becomes r"^\/hello\/(?P<name>[^\^.]+)$"

    For /hello/{name:pattern} 
    you get whatever is in self.patterns['pattern'] instead of "[^\^.]+"

    Optional portions of path expression can be expressed [like this]

    /hello/{name}[/] (can have trailing slash or not)

    Example:

    /blog/archive/{year:digits}/{month:digits}[/[{article}[/]]]

    This would catch any of these:

    /blog/archive/2005/09
    /blog/archive/2005/09/
    /blog/archive/2005/09/1
    /blog/archive/2005/09/1/

    (I am not suggesting that this example is a best practice.
    I would probably have a separate mapping for listing the month
    and retrieving an individual entry. It depends, though.)
    """

    start, end = '{}'
    ostart, oend = '[]'
    _patterns = {'word': r'\w+',
                 'alpha': r'[a-zA-Z]+',
                 'digits': r'\d+',
                 'number': r'\d*.?\d+',
                 'chunk': r'[^/^.]+',
                 'segment': r'[^/]+',
                 'custom': r'[^/^;]+',  # toby
                 'any': r'.+'}
    default_pattern = 'chunk'
    
    def __init__(self, patterns=None):
        """Initialize with character class mappings."""
        self.patterns = dict(self._patterns)
        if patterns is not None:
            self.patterns.update(patterns)

    def lookup(self, name):
        """Return the replacement for the name found."""
        if ':' in name:
            name, pattern = name.split(':')
            pattern = self.patterns[pattern]
        else:
            pattern = self.patterns[self.default_pattern]
        return '(?P<%s>%s)' % (name, pattern)

    def lastly(self, regex):
        """Process the result of __call__ right before it returns.
        
        Adds the ^ and the $ to the beginning and the end, respectively.
        """
        return "^%s$" % regex

    def outermost_optionals_split(self, text):
        """Split out optional portions by outermost matching delims."""
        parts = []
        buffer = ""
        starts = ends = 0
        for c in text:
            if c == self.ostart:
                if starts == 0:
                    parts.append(buffer)
                    buffer = ""
                else:
                    buffer += c
                starts +=1
            elif c == self.oend:
                ends +=1
                if starts == ends:
                    parts.append(buffer)
                    buffer = ""
                    starts = ends = 0
                else:
                    buffer += c
            else:
                buffer += c
        if not starts == ends == 0:
            raise PathExpressionParserError(
                "Mismatch of optional portion delimiters."
            )
        parts.append(buffer)
        return parts

    def parse(self, text):
        """Turn a path expression into regex."""
        if self.ostart in text:
            parts = self.outermost_optionals_split(text)
            parts = map(self.parse, parts)
            parts[1::2] = ["(%s)?" % p for p in parts[1::2]]
        else:
            parts = [part.split(self.end) 
                     for part in text.split(self.start)]
            parts = [y for x in parts for y in x]
            parts[::2] = map(re.escape, parts[::2])
            parts[1::2] = map(self.lookup, parts[1::2])
        return ''.join(parts)

    def __call__(self, url_pattern):
        """Turn a path expression into regex via parse and lastly."""
        return self.lastly(self.parse(url_pattern))


class EnvironDispatcher(object):
    """Dispatch based on list of rules."""

    def __init__(self, rules):
        """Instantiate with a list of (predicate, wsgiapp) rules."""
        self.rules = rules

    def __call__(self, environ, start_response):
        """Call the first app whose predicate is true.
        
        Each predicate is passes the environ to evaluate.
        """
        for predicate, app in self.rules:
            if predicate(environ):
                return app(environ, start_response)


class MiddlewareComposer(object):
    """Compose middleware based on list of rules."""

    def __init__(self, app, rules):
        """Instantiate with an app and a list of rules."""
        self.app = app
        self.rules = rules

    def __call__(self, environ, start_response):
        """Apply each middleware whose predicate is true.
        
        Each predicate is passes the environ to evaluate.

        Given this set of rules:
        
        t = lambda x: True; f = lambda x: False
        [(t, a), (f, b), (t, c), (f, d), (t, e)]

        The app composed would be equivalent to this:

        a(c(e(app)))
        """
        app = self.app
        for predicate, middleware in reversed(self.rules):
            if predicate(environ):
                app = middleware(app)
        return app(environ, start_response)


