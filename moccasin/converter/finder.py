#!/usr/bin/env python
#
# @file    finder.py
# @brief   Find things in a MatlabNode tree
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

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

from moccasin.matlab_parser import *


class MatlabFinder(MatlabNodeVisitor):
    def __init__(self, context):
        super(MatlabFinder, self).__init__()
        self._context = context
        self._found = []
        self._seek_symbol = None
        self._seek_operators = []


    def visit_FunCall(self, node):
        if self._seek_symbol and node.args and self._seek_symbol in node.args:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.args)


    def visit_FunDef(self, node):
        # Need to be careful about scoping.  If there are inner functions,
        # then we do want to descend into them; if they're inner functions,
        # they will appear as FunDef objects in the body of this function, so
        # visiting the body is all we need to do.  However, if there are
        # local functions in the file, then they will not appear as FunDefs
        # in the body here, and we won't descend into them, and that's correct.
        if node.body:
            self.visit(node.body)


    def visit_Assignment(self, node):
        if self._seek_symbol and node.rhs == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.rhs)


    def visit_Operator(self, node):
        if hasattr(node, 'op') and node.op in self._seek_operators:
            self._found.append(node.op)
            return
        if hasattr(node, 'operand'):
            if self._seek_symbol and node.operand == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.operand)
        if hasattr(node, 'left'):
            if self._seek_symbol and node.left == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.left)
        if hasattr(node, 'right'):
            if self._seek_symbol and node.right == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.right)
        if hasattr(node, 'middle'):
            if self._seek_symbol and node.middle == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.middle)


    def visit_If(self, node):
        if self._seek_symbol and node.cond == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.cond)
        if self._seek_symbol and node.body == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.body)
        if self._seek_symbol and node.else_body == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.else_body)
        for else_cond, else_body in (node.elseif_tuples or []):
            if self._seek_symbol and else_cond == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(else_cond)
            if self._seek_symbol and else_body == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(else_body)


    def visit_Switch(self, node):
        if self._seek_symbol and node.cond == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.cond)
        if self._seek_symbol and node.otherwise == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.otherwise)
        for case_cond, case_body in (node.case_tuples or []):
            if self._seek_symbol and case_cond == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(case_cond)
            if self._seek_symbol and case_body == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(case_body)


    def visit_FlowControl(self, node):
        # This handles the remaining flow control constructs like while & for.
        if hasattr(node, 'cond'):
            if self._seek_symbol and node.cond == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.cond)
        if hasattr(node, 'expr'):
            if self._seek_symbol and node.expr == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.expr)
        if hasattr(node, 'body'):
            if self._seek_symbol and node.body == self._seek_symbol:
                self._found.append(self._seek_symbol)
                return
            else:
                self.visit(node.body)


    def visit_Array(self, node):
        for row in (node.rows or []):
            for item in (row or []):
                if self._seek_symbol and item == self._seek_symbol:
                    self._found.append(self._seek_symbol)
                    return
                else:
                    self.visit(item)


    def visit_ArrayRef(self, node):
        if self._seek_symbol and node.name == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        elif not isinstance(node.name, Identifier):
            self.visit(node.name)
        if self._seek_symbol and node.args and self._seek_symbol in node.args:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.args)


    def visit_Ambiguous(self, node):
        if self._seek_symbol and node.name == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        elif not isinstance(node.name, Identifier):
            self.visit(node.name)
        if self._seek_symbol and node.args and self._seek_symbol in node.args:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.args)


    def visit_StructRef(self, node):
        if self._seek_symbol and node.name == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        elif not isinstance(node.name, Identifier):
            self.visit(node.name)


    def visit_AnonFun(self, node):
        if self._seek_symbol and node.body == self._seek_symbol:
            self._found.append(self._seek_symbol)
            return
        else:
            self.visit(node.body)


    def find_symbol(self, var):
        self._seek_symbol = var
        self.visit(self._context.nodes)
        return self._found


    def find_operators(self, ops):
        self._seek_operators = ops
        self.visit(self._context.nodes)
        return self._found
