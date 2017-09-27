#!/usr/bin/env python
#
# @file    cleaner.py
# @brief   Remove some MATLAB content that we can't process.
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
sys.path.append('..')
from matlab_parser import *

# MatlabCleaner
#
# Some things, like calls to figure and plotting commands, are never anything
# we need to process in MOCCASIN.  We can remove them from the input and save
# time and confusion in later processing steps.

_ignorable = [
    'annotation'
    'area',
    'axes',
    'axis',
    'bar',
    'bar3',
    'bar3h',
    'barh',
    'box',
    'caxis',
    'celldisp',
    'cellplot',
    'cla',
    'clc',
    'clabel',
    'clear',
    'close',
    'colorbar',
    'colordef',
    'colormap',
    'coneplot',
    'countour',
    'countour3',
    'countourc',
    'countourf',
    'countourslice',
    'daspect',
    'datetick',
    'diary',
    'disp',
    'errorbar',
    'etreeplot',
    'ezcontour',
    'ezcontourf',
    'fcontour',
    'figure',
    'figurepalette',
    'fill',
    'fill3',
    'format',
    'fplot',
    'fplot3',
    'fprintf',
    'fscanf',
    'gca',
    'gplot',
    'grid',
    'gtext',
    'histcounts',
    'histcounts2',
    'histogram',
    'histogram2',
    'hold',
    'legend',
    'line',
    'loglog',
    'mesh',
    'meshc',
    'meshgrid',
    'odeset',
    'patch',
    'pie',
    'pie3',
    'plot',
    'plot3',
    'plotmatrix'
    'polaraxes',
    'polarplot',
    'print',
    'printf',
    'rectangle',
    'refresh',
    'rlim',
    'rgbplot',
    'scatter',
    'scatter3',
    'semilogx',
    'semilogy',
    'set',
    'sprintf',
    'stairs'
    'stem',
    'stem3',
    'subplot',
    'surf',
    'surf2patch',
    'surface',
    'surfc',
    'surfl',
    'surfnorm',
    'text',
    'textlabel',
    'thetalim',
    'title',
    'treelayout',
    'unmesh',
    'xlabel',
    'xlim',
    'ylabel',
    'ylim',
    'yyaxis',
    'zlabel',
    'zlim',
    'zoom',
    ]


class MatlabCleaner(MatlabNodeVisitor):
    def __init__(self):
        super(MatlabCleaner, self).__init__()


    def _push_context(self, newcontext):
        self._context = newcontext


    def _pop_context(self):
        # Don't pop topmost context.
        if self._context.parent and not self._context.topmost:
            self._context = self._context.parent


    def visit_Assignment(self, node):
        # Catches assignments where the RHS is a call to something ignorable.
        # The whole assignmet can be ignored in that case.
        rhs = node.rhs
        if (isinstance(rhs, FunCall) and isinstance(rhs.name, Identifier)
            and rhs.name.name in _ignorable):
            # Remove the assignment from the context too.
            if (isinstance(node.lhs, Identifier)
                and node.lhs in self._context.assignments):
                self._context.assignments.pop(node.lhs)
            return None
        if rhs is None:
            # This happens if something else has taken out the RHS already.
            return None
        return node


    def visit_FunCall(self, node):
        # This catches top-level calls to things like 'figure', 'plot', etc.
        if isinstance(node.name, Identifier) and node.name.name in _ignorable:
            return None
        return node


    def visit_FunDef(self, node):
        # Push the new function context.  Note that FunDef is unusual in having
        # a node.context property -- other MatlabNodes don't.
        self._push_context(node.context)
        self._context.nodes = self.visit(self._context.nodes)
        node.body = self._context.nodes
        self._pop_context()
        return node


    def visit_For(self, node):
        # We could potentially handle simple loops like "for x in 1:n" if we
        # could determine the number of times the loop body should be
        # executed.  Right now, Moccasin is not smart enough to do that.
        # Since it doesn't make sense to execute the loop an arbitrary number
        # of times rather than the number of times in the user's Matlab code,
        # we just ignore loops completely, and we tell people not to use
        # loops.
        node.expr = []
        node.body = None
        return None
