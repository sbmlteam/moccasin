#!/usr/bin/env python
#
# @file    grammar_utils.py
# @brief   Utilities used by our PyParsing grammar for MATLAB
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2017 jointly by the following organizations:
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

import functools
import inspect
import sys
import six
from pyparsing import ParseResults

#
# Parsing helpers.
# .............................................................................

# makeLRlike -- function used in the definition of our grammar in grammar.py

def makeLRlike(numterms):
    """Parse action that will take flat lists of tokens and nest them
    as if parsed left-recursively.  Originally written by Paul McGuire as
    a StackOverflow answer here: http://stackoverflow.com/a/4589920/743730
    """
    initlen = {0: 1, 1: 2, 2: 3, 3: 5}[numterms]
    incr = {0: 1, 1: 1, 2: 2, 3: 4}[numterms]

    # Create a closure.  This defines a parse action for this number of
    # terms, to convert flat list of tokens into nested list.
    def pa(s, l, t):
        t = t[0]
        if len(t) > initlen:
            ret = ParseResults(t[:initlen])
            i = initlen
            while i < len(t):
                ret = ParseResults([ret] + t[i:i + incr])
                i += incr
            return ParseResults([ret])

    # Return the closure.
    return pa


# From http://pyparsing.wikispaces.com/share/view/41237655

def setVar(varname, varvalue):
    def parseAction(tokens):
        tokens[varname] = varvalue
    return parseAction


#
# Debug helpers
# .............................................................................

# Extremely helpful debugging aid posted by Florian Brucker posted to
# http://stackoverflow.com/a/24743279/743730
#
# Usage example:
#   @parse_debug_helper
#   def some_parse_action(tokens):
#       ....
#
# where "some_parse_action" is a method you attach via setParseAction(...) to
# some part of your pyparsing grammar.
#
def parse_debug_helper(f):
    """Decorator for pyparsing parse actions to ease debugging.

    pyparsing uses trial & error to deduce the number of arguments a
    parse action accepts. Unfortunately any ``TypeError`` raised by a
    parse action confuses that mechanism.

    This decorator replaces the trial & error mechanism with one based on
    reflection. If the decorated function itself raises a ``TypeError``
    then that exception is re-raised if the wrapper is called with less
    arguments than required. This makes sure that the actual
    ``TypeError`` bubbles up from the call to the parse action (instead
    of the one caused by pyparsing's trial & error).
    """
    num_args = len(inspect.getargspec(f).args)
    if num_args > 3:
        raise ValueError('Input function must take no more than 3 parameters.')

    @functools.wraps(f)
    def action(*args):
        if len(args) < num_args:
            if action.exc_info:
                raise six.reraise(action.exc_info[0], action.exc_info[1],
                                  action.exc_info[2])
        action.exc_info = None
        try:
            return f(*args[:-(num_args + 1):-1])
        except TypeError as e:
            action.exc_info = sys.exc_info()
            raise

    action.exc = None
    return action


# Portability helpers.
# .............................................................................

def first_key(d):
    if sys.version < '3':
        return sorted(d.keys())[0]
    else:
        for key in sorted(d.keys()):
            return key


def num_keys(d):
    return len(list(d.keys()))


def empty_dict(d):
    return not (d.keys() and len(list(d.keys())) > 0)
