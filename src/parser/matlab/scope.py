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

class Scope:
    def __init__(self, name='', parent=None, pr=None, args=[], returns=[]):
        self.assignments   = dict()
        self.functions     = dict()
        self.calls         = dict()
        self.name          = name
        self.parent        = parent
        self.args          = args     # If this is a function, its args.
        self.returns       = returns  # If this is a function, return values.
        self.comments      = []       # Comments ahead of this function.
        self.parse_results = pr


    def copy_scope(self, source):
        if not isinstance(source, Scope):
            raise TypeError('Expected a Scope object')
        self.assignments   = source.assignments
        self.functions     = source.functions
        self.calls         = source.calls
        self.name          = source.name
        self.parent        = source.parent
        self.args          = source.args
        self.returns       = source.returns
        self.comments      = source.comments
        self.parse_results = source.parse_results


    def add_function_definition(self, name, args, output, pr):
        if args:
            args = args.asList()
        if output:
            output = output.asList()
        self.functions[name] = {'args': args, 'output': output, 'parse' : pr}


    def add_variable_assignment(self, name, value):
        self.assignments[name] = value


    def add_function_call(self, name, args):
        self.calls[name] = args
