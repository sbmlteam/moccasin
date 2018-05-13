#!/usr/bin/env python
#
# @file    expr_tester.py
# @brief   Recognize if an expression evaluates to a numeric constant.
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

# MatlabExprTester
#
# We need to recognize the user of a variable that refers to time, because it
# will need to be handled specially in the MOCCASIN conversion procedure.  This
# code is a general system that hopefully can be extended in the future for
# other constructs if we ever need to do that.

class MatlabExprTester(MatlabNodeVisitor):
    def __init__(self, context):
        super(MatlabExprTester, self).__init__()
        self._context = context
        self._is_constant = True


    def visit_Reference(self, node):
        self._is_constant = False
        return node


    def visit_Definition(self, node):
        self._is_constant = False
        return node


    def is_constant(self):
        return self._is_constant
