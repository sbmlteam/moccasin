#!/usr/bin/env python
#
# @file    scope.py
# @brief   Object to hold information about a function or file
# @author  Michael Hucka
#
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.

import collections
from pyparsing import ParseResults


# This next class def is courtesy of http://stackoverflow.com/a/7760938/743730
#
class ScopeDict(collections.MutableMapping, dict):
    '''Class used to implement Scope properties that are dictionaries.'''

    def __setitem__(self, key, val):
        self._dict[key] = val

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def __iter__(self):
        return dict.__iter__(self)

    def __len__(self):
        return dict.__len__(self)

    def __contains__(self, x):
        return dict.__contains__(self, x)


class Scope:

    def __init__(self, name='', parent=None, pr=None, args=[], returns=[]):
        self.name          = name       # Name of this scope.
        if isinstance(args, ParseResults):
            self.args      = args.asList()
        else:
            self.args      = args       # If this is a function, its arg list.
        if isinstance(returns, ParseResults):
            self.returns   = returns.asList()
        else:
            self.returns   = returns    # If this is a function, return values.
        self.comments      = []         # Comments ahead of this function.
        self.parent        = parent     # Parent scope containing this one.
        self.parse_results = pr
        self._functions    = ScopeDict()
        self._variables    = ScopeDict()
        self._calls        = ScopeDict()


    def __repr__(self):
        parent_name = ''
        if self.parent:
            parent_name = self.parent.name
        s = '<scope "{0}": {1} func defs, {2} vars, {3} calls, parent = "{4}">'
        return s.format(self.name, len(self._functions), len(self._variables),
                        len(self._calls), parent_name)


    def copy_scope(self, source):
        if not isinstance(source, Scope):
            raise TypeError('Expected a Scope object')
        self.name          = source.name
        self.args          = source.args
        self.returns       = source.returns
        self.comments      = source.comments
        self.parent        = source.parent
        self.parse_results = source.parse_results
        self._functions    = source._functions
        self._variables    = source._variables
        self._calls        = source.calls


    @property
    def functions(self):
        return self._functions


    @functions.setter
    def functions(self, key, value):
        if not isinstance(value, Scope):
            raise ValueError("Functions values must be Scope objects")
        else:
            self._functions[name] = value


    @functions.getter
    def functions(self):
        return self._functions


    @property
    def variables(self):
        return self._variables


    @variables.setter
    def variables(self, key, value):
        self._variables[key] = value


    @variables.getter
    def variables(self):
        return self._variables


    @property
    def calls(self):
        return self._calls


    @calls.setter
    def calls(self, key, value):
        self._calls[key] = value


    @calls.getter
    def calls(self):
        return self._calls


# Quick testing interface.

if __name__ == '__main__':
    x = Scope('scope x')
    y = Scope('scope y', x)
    z = Scope('scope y', y)
    z.variables['var1'] = 111
    z.variables['var2'] = 222
    try:
        print 'x = ' + str(x)
        print 'y = ' + str(y)
        print 'z = ' + str(z)
    except Exception as err:
        print("error: {0}".format(err))
