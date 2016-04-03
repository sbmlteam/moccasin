#!/usr/bin/env python
#
# @file    rewriter.py
# @brief   Transform some MATLAB into other MATLAB
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

import sys
sys.path.append('..')
from matlab_parser import *

# MatlabRewriter
#
# We need to reformulate some MATLAB expressions into equivalent forms that
# can be stored in SBML files.  Some things are easy to do and can be done
# by changing the parsing results at the level of the MatlabNode tree returned
# by our MOCCASIN parser.  This implements those transformations.

class MatlabRewriter(MatlabNodeVisitor):
    def __init__(self):
        super(MatlabRewriter, self).__init__()


    def visit_FunCall(self, node):
        if isinstance(node.name, Identifier):
            methname = 'matlab_' + node.name.name
            meth = getattr(self, methname, None)
            return meth(node) if meth else node


    def matlab_zeros(self, thing):
        # Function calls like zeros(3,1) produces a matrix.  This generates
        # the equivalent expanded form.
        args = thing.args
        if len(args) == 1:
            rows = int(args[0].value)
            return Array(rows=[[Number(value='0')]]*rows, is_cell=False)
        elif len(args) == 2:
            rows = int(args[0].value)
            cols = int(args[1].value)
            return Array(rows=[[Number(value='0')]*cols]*rows, is_cell=False)
        # Fall back: make sure to return *something*.
        return thing


    def matlab_log(self, thing):
        # Matlab's log(x) is natural log of x, but libSBML's parser defaults
        # to base 10.  This converts it to ln, libSBML's name for natural log.
        args = thing.args
        if len(args) == 1:
            return FunCall(name=Identifier(name="ln"), args=[args[0]])
        # Fall back: make sure to return *something*.
        return thing
