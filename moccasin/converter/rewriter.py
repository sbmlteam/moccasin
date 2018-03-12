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

import sys
from decimal import *

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

from moccasin.matlab_parser import *

# MatlabRewriter
#
# We need to reformulate some MATLAB expressions into equivalent forms that
# can be stored in SBML files.  Some things are easy to do and can be done
# by changing the parsing results at the level of the MatlabNode tree returned
# by our MOCCASIN parser.  This implements those transformations.
#
# This also implements other transformations that may be necessary, such as
# converting the format of numbers to something that XPP and Biocham can handle.

class MatlabRewriter(MatlabNodeVisitor):

    def __init__(self, context, output_format):
        super(MatlabRewriter, self).__init__()
        self.output_format = output_format
        self.unscientific_numbers = (output_format in ['xpp', 'biocham'])
        self._context = context


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
        self._context.nodes = self.visit(self._context.nodes)
        node.body = self._context.nodes
        self._pop_context()
        return node


    def visit_FunCall(self, node):
        node.args = self.visit(node.args)
        if isinstance(node.name, Identifier):
            methname = 'matlab_' + node.name.name
            meth = getattr(self, methname, None)
            return meth(node) if meth else node


    def visit_Number(self, node):
        # Biocham seems unable to parse numbers in scientific notation in
        # some cases, and I haven't figured out what XPP is doing with
        # precision for numbers like 1.25e-7, which it displays as 0.000000.
        if self.unscientific_numbers:
            # Convert to a non-scientific number representation.
            value = node.value
            if 'e' in value or 'E' in value or 'd' in value or 'D' in value:
                tmp = Decimal(value)
                exponent = tmp.as_tuple().exponent
                if exponent < 0:
                    size = abs(exponent)
                    node.value = '{0:.{1}f}'.format(tmp, size)
                else:
                    node.value = '{:f}'.format(tmp)
            # If I hand Biocham a number like "10.", it stops parsing the input.
            if node.value.endswith('.'):
                node.value = node.value[:-1]
            if node.value.startswith('.'):
                node.value = '0' + node.value
        return node


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


    def matlab_ones(self, thing):
        # Function calls like ones(3,1) produces a matrix.  This generates
        # the equivalent expanded form.
        args = thing.args
        if len(args) == 1:
            rows = int(args[0].value)
            return Array(rows=[[Number(value='1')]]*rows, is_cell=False)
        elif len(args) == 2:
            rows = int(args[0].value)
            cols = int(args[1].value)
            return Array(rows=[[Number(value='1')]*cols]*rows, is_cell=False)
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


    def matlab_pi(self, thing):
        # When pi is encountered, it is turned into a function call with no
        # arguments (good), but this is then not recognized by libSBML's
        # parser as being a reference to the predefined constant 'pi' (bad).
        # LibSBML is not at fault here -- this is a quirk because Matlab uses
        # a function for pi, rather than a variable.  We patch things up here.
        return Identifier(name='pi')
