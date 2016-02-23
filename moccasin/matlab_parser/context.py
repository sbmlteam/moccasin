#!/usr/bin/env python
#
# @file    context.py
# @brief   Object to hold information about a MATLAB function or file.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2015 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

from __future__ import print_function
import collections
from pyparsing import ParseResults


# The ContextDict class makes it easier to create dictionary-like properties
# on MatlabContext objects.  The reason it's necessary is that Python
# properties are designed around the idea that you do "obj.prop = value",
# whereas for some properties in MatlabContext, we want the ability to do
# "obj.prop[key] = value".  This means that obj.prop has to be a custom class
# that supports the operations.
#
# This next class def is based on http://stackoverflow.com/a/7760938/743730

class ContextDict(collections.MutableMapping, dict):
    '''Class used to implement MatlabContext properties that are dictionaries.'''

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


class MatlabContext(object):
    '''Class for tracking our interpretation of MATLAB parsing results.  Most
    properties of objects of this class are used to store things that are
    also in one of our annotated ParseResults structures, but designed to
    make it easier to access data that we need for our MATLAB translation
    purposes.  Some properties are things that aren't from ParseResults, such
    as a link to the parent context.

    The properties are:

      topmost:     Boolean; True if this is the top-most context in the file.

      name:        The name of this context.  If this context represents a
                   function definition, it will be the function name.  If this
                   is the topmost context, the name will be the name of the
                   first function defined in the file.

      parent:      The parent context object.  If this is the top-most context
                   in the file, this value will be None.

      nodes:       The parsed representation of the MATLAB code within this
                   context, expressed as a list of MatlabNode objects.  If this
                   context is a script file, then it's the list of statements in
                   the file; if it's a function, it's the list of statements in
                   the function's body.

      parameters:  If this is a function, a list of the parameters it takes.
                   The list will contain MatlabNode objects.

      returns:     If this is a function, its return values.  The list will
                   contain MatlabNode objects.

      functions:   A dictionary of functions defined within this context.  The
                   keys are the function names; the values are Context objects
                   for the functions.

      assignments: A dictionary of the assignment statements within this
                   context.  For simple variables (a = ...), the keys are the
                   variable names.  In the case of arrays, the keys are
                   assumed to be string representations of the array, with
                   the following features.  If it's a bare matrix, square
                   braces surround the matrix, semicolons separate rows,
                   commas separate index terms within rows, and all spaces
                   are removed.  If it's a matrix reference, it is similar
                   but starts with a name and uses regular parentheses
                   instead of square braces.  So, e.g., [a b] is turned into
                   '[a,b]', '[ a ; b ; c]' is turned into '[a;b;c]', 'foo(1,
                   2)' is turned into 'foo(1,2)', and so on.  The dict values
                   are the MatlabNode objects for the RHS.

      types:       A dictionary of data types associated with objects.  For
                   example, when MatlabGrammar encounters an assignment
                   statement or a function definition, it stores the
                   identifier of the assigned variable or parameter in this
                   dictionary and sets the value to 'variable', to distinguish
                   it from a 'function'.

      calls:       A dictionary of functions called within this context.  The
                   keys are the function names; the values is a list of the
                   arguments (as annotated ParseResults objects).

      pr:          The pr object related to this context.  This Context
                   will contain the stuff from which we constructed this
                   instance of a Context object.  The representation is awkward
                   and not meant to be used by callers, but it's left around
                   for debugging purposes.

      file:        If the contents of this context came from a file, the path
                   to the file.

    Users can access via the normal x.propname approach.

    To make a copy of a Context object, use the Python 'copy' module.
    '''

    def __init__(self, name=None, parent=None, nodes=None, parameters=[],
                 returns=[], pr=None, file=None, topmost=False):
        self.topmost        = topmost    # Whether this is the top context.
        self.name           = name       # Name of this context.
        self.parameters     = parameters # Arg list, if this is a function.
        self.returns        = returns    # If this is a function, return values.
        self.comments       = []         # Comments ahead of this function.
        self.parent         = parent     # Parent context containing this one.
        self.nodes          = nodes      # The list of MatlabNode objects.
        self.parse_results  = pr         # The corresponding ParseResults obj.
        self.file           = file       # The path to the file, if any.
        self._functions     = ContextDict()
        self._assignments   = ContextDict()
        self._calls         = ContextDict()
        self._types         = ContextDict()


    def __repr__(self):
        parent_name = ''
        if self.parent:
            parent_name = self.parent.name
        s = '<context "{0}"{1}: {2} func, {3} assign, {4} calls, parent = {5}, file = "{6}">'
        return s.format(self.name, " (top)" if self.topmost else '',
                        len(self._functions), len(self._assignments),
                        len(self._calls), parent_name, self.file)


    @property
    def functions(self):
        '''Allows access to the 'functions' property as a dictionary.'''
        return self._functions


    @functions.setter
    def functions(self, key, value):
        if not isinstance(value, Context):
            raise ValueError("Functions values must be MatlabContext objects")
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


    @property
    def types(self):
        '''Allows access to the 'types' property as a dictionary.'''
        return self._types


    @types.setter
    def types(self, key, value):
        self._types[key] = value


    @types.getter
    def types(self):
        return self._types



# Quick testing interface.

if __name__ == '__main__':
    x = MatlabContext('context x')
    y = MatlabContext('context y', x)
    z = MatlabContext('context y', y)
    z.assignments['var1'] = 111
    z.assignments['var2'] = 222

    try:
        print('x = ' + str(x))
        print('y = ' + str(y))
        print('z = ' + str(z))
    except Exception as err:
        print("error: {0}".format(err))
