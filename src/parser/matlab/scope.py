#!/usr/bin/env python
#
# @file    scope.py
# @brief   Object to hold information about a function or file
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
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
# ------------------------------------------------------------------------- -->

import collections
from pyparsing import ParseResults


# The ScopeDict clas makes it easier to create dictionary-like properties on
# Scope objects.  The reason it's necessary is that Python properties are
# designed around the idea that you do "obj.prop = value", whereas for some
# properties in Scope, we want the ability to do "obj.prop[key] = value".  This
# means that obj.prop has to be a custom class that supports the operations.
#
# This next class def is based on http://stackoverflow.com/a/7760938/743730

class ScopeDict(collections.MutableMapping, dict):
    '''Class used to implement Scope properties that are dictionaries.'''

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
    '''Class for tracking our interpretation of MATLAB parsing results.  Most
    properties of objects of this class are used to store things that are
    also in one of our annotated ParseResults structures, but designed to
    make it easier to access data that we need for our MATLAB translation
    purposes.  Some properties are things that aren't from ParseResults, such
    as a link to the parent scope.

    The properties are:

      name:        The name of this scope.  If this is a function, it will be
                   its name; otherwise, it will be something else indicating
                   the scope.

      parent:      The parent scope object.

      pr:          The ParseResults object related to this scope.  This Scope
                   will contain the stuff from which we constructed this
                   instance of a Scope object.

      args:        If this is a function, a list of the arguments it takes.
                   This list contains just symbol names, not parse objects.

      returns:     If this is a function, its return values.  This list
                   contains just symbol names, not parse objects.

      functions:   A dictionary of functions defined within this scope.  The
                   keys are the function names; the values are Scope objects
                   for the functions.

      assignments: A dictionary of the assignment statements within this
                   scope.  For simple variables (a = ...), the keys are the
                   variable names.  In the case of matrices, the keys are
                   assumed to be string representations of the matrix, with
                   the following features.  If it's a bare matrix, square
                   braces surround the matrix, semicolons separate rows,
                   commas separate index terms within rows, and all spaces
                   are removed.  If it's a matrix reference, it is similar
                   but starts with a name and uses regular parentheses
                   instead of square braces.  So, e.g., [a b] is turned into
                   '[a,b]', '[ a ; b ; c]' is turned into '[a;b;c]', 'foo(1,
                   2)' is turned into 'foo(1,2)', and so on.  The dict values
                   are the ParseResults objects for the RHS.

      calls:       A dictionary of functions called within this scope.  The
                   keys are the function names; the values is a list of the
                   arguments (as annotated ParseResults objects).

    Users can access via the normal x.propname approach.

    '''

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
        self.parse_results = pr         # The corresponding ParseResults obj.
        self._functions    = ScopeDict()
        self._assignments  = ScopeDict()
        self._calls        = ScopeDict()


    def __repr__(self):
        parent_name = ''
        if self.parent:
            parent_name = self.parent.name
        s = '<scope "{0}": {1} func defs, {2} assignments, {3} calls, parent = "{4}">'
        return s.format(self.name, len(self._functions), len(self._assignments),
                        len(self._calls), parent_name)


    def copy_scope(self, source):
        '''Reset all properties of the current object to those of source's.'''
        if not isinstance(source, Scope):
            raise TypeError('Expected a Scope object')
        self.name          = source.name
        self.args          = source.args
        self.returns       = source.returns
        self.comments      = source.comments
        self.parent        = source.parent
        self.parse_results = source.parse_results
        self._functions    = source._functions
        self._assignments  = source._assignments
        self._calls        = source._calls


    @property
    def functions(self):
        '''Allows access to the 'functions' property as a dictionary.'''
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
    def assignments(self):
        '''Allows access to the 'assignments' property as a dictionary.'''
        return self._assignments


    @assignments.setter
    def assignments(self, key, value):
        self._assignments[key] = value


    @assignments.getter
    def assignments(self):
        return self._assignments


    @property
    def calls(self):
        '''Allows access to the 'calls' property as a dictionary.'''
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
    z.assignments['var1'] = 111
    z.assignments['var2'] = 222

    try:
        print 'x = ' + str(x)
        print 'y = ' + str(y)
        print 'z = ' + str(z)
    except Exception as err:
        print("error: {0}".format(err))
