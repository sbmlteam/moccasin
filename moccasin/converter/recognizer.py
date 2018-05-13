#!/usr/bin/env python
#
# @file    recognizer.py
# @brief   Recognize some MATLAB constructs and report if they're used
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2018 jointly by the following organizations:
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

import sys
from collections import defaultdict

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

from moccasin.matlab_parser import *

# MatlabRecognizer
#
# We need to recognize the user of a variable that refers to time, because it
# will need to be handled specially in the MOCCASIN conversion procedure.  This
# code is a general system that hopefully can be extended in the future for
# other constructs if we ever need to do that.
#
# FIXME: this is really specific to finding 't' for time right now.

class MatlabRecognizer(MatlabNodeVisitor):
    def __init__(self, context):
        super(MatlabRecognizer, self).__init__()
        self._context = context

        # Add new variations on identifiers as values of the lists here.
        self._identifier_mapping = {'time': ['t'], 'pi': ['pi']}

        # The rest below should not need to change.
        self._found = dict.fromkeys(self._identifier_mapping.keys(), [])
        self._identifiers_sought = [x for sublist in self._identifier_mapping.values()
                                    for x in sublist]


    def _push_context(self, newcontext):
        self._context = newcontext


    def _pop_context(self):
        # Don't pop topmost context.
        if self._context.parent and not self._context.topmost:
            self._context = self._context.parent


    def visit_FunDef(self, node):
        # Push the new function context.  Note that FunDef is unusual in having
        # a node.context property -- other MatlabNodes don't.
        self._push_context(node.context)
        # We don't consider parameters.
        if node.body:
            self.visit(node.body)
        if node.output:
            self.visit(node.output)
        self._pop_context()
        return node


    def visit_Identifier(self, node):
        if self._context.name and self._context.name in self._context.functions:
            # Owing to how most people write the ODE functions, we don't
            # simply look for any reference to an identifier named 't'
            # because the ODE function definitions usually have 't' as their
            # first parameter.  So, ignore parameter names in function defs.
            if node in self._context.functions[self._context.name].parameters:
                return node
        for key, value in self._identifier_mapping.items():
            if node.name in value:
                self._found[key].append(node)
                break
        return node


    def visit_Assignment(self, node):
        # A model can't reassign time (what would that mean, anyway?), but
        # the form of the ODE calls we are looking for typically have 't' in
        # the LHS, like this:
        #    [t, y] = ode45(@f, tspan, x0)
        # This is not a reason to think that 't' is being used in the model.
        # So, we purposefully only walk down the RHS of assignments.
        #
        # FIXME: this only is valid when we're looking for 't' for time!  If
        # this class ever gets expanded to handle more things, then this code
        # must be revised.
        self.visit(node.rhs)
        return node


    def found(self, key):
        if key not in self._identifier_mapping:
            return ValueError(key + ' is not a recognized variable')
        return self._found[key] if key in self._found else None
