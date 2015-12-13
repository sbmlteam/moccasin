#!/usr/bin/env python
#
# @file    matlab.py
# @brief   Objects to represent a parsed version of MATLAB code.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
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
import sys
import pdb
import collections


# MatlabNode -- base class for all parse tree nodes.
# .........................................................................

class MatlabNode(object):
    _attr_names = None                 # Default set of node attributes.
    _visitable_attr = []               # Default list of visitable attributes.
    _location   = (0, 0)               # Location in file (tuple: line, col).

    # The following is based on code in Section 8.11 of the Python Cookbook,
    # 3rd ed., by David Beazley and Brian K. Jones (O'Reilly Media, 2013).
    def __init__(self, *args, **kwargs):
        if not self._attr_names:
            if len(args) > 0 or len(kwargs) > 0:
                raise TypeError('{} takes no arguments'.format(type(self)))
            else:
                return

        # Set all of the positional arguments:
        for name, value in zip(self._attr_names, args):
            setattr(self, name, value)

        # Set the remaining keyword arguments:
        for name in self._attr_names[len(args):]:
            setattr(self, name, kwargs.pop(name))

        # Check for any remaining unknown arguments:
        if kwargs:
            raise TypeError('Invalid argument(s): {}'.format(','.join(kwargs)))


    def __repr__(self):
        return 'MatlabNode()'


    def __str__(self):
        return '{MatlabNode}'


# Expressions -- parent class of operators and other things in expressions.
# .........................................................................

class Expression(MatlabNode):
    '''Parent class for expressions.'''
    pass



# Entity -- parent class of things that show up in expressions.
# .........................................................................

class Entity(Expression):
    '''Parent class for entities in expressions.'''

    def __repr__(self):
        return 'Entity()'


#
# Primitive entities.
#
# All primitive entities have a single attribute named "value".
#

class Primitive(Entity):
    '''Parent class for primitive terms, such as numbers and strings.'''
    _attr_names = ['value']

    def __repr__(self):
        return '{}(value={})'.format(self.__class__.__name__, repr(self.value))

    def __str__(self):
        return '{{{}: {}}}'.format(self.__class__.__name__.lower(), self.value)


class Number(Primitive):
    '''Any numerical value.  Note that it is stored as a text string.'''
    pass


class Boolean(Primitive):
    '''A Boolean value.'''
    pass


class String(Primitive):
    '''A text string.'''

    # Overrides default printer to put double quotes around value.
    def __str__(self):
        return '{{string: "{}"}}'.format(self.value)


class Special(Primitive):
    '''A literal ~, :, or "end" used in an array context.'''

    # This is not strictly necessary, but the old printer/formatter in
    # grammar.py did it this way, so I'm repeating it here to make comparing
    # results easier.
    def __str__(self):
        if self.value == ':':
            return '{colon}'
        elif self.value == '~':
            return '{tilde}'
        elif self.value == 'end':
            return '{end}'


#
# Bare arrays.
#
# This represents either unnamed, square-bracket delimited arrays, or
# unnamed cell arrays.  They are here because they are half-way between
# primitive values and named things.
#

class Array(Entity):
    '''The field `is_cell` is True if this is a cell array.'''
    _attr_names = ['is_cell', 'rows']
    _visitable_attr = ['rows']

    def __repr__(self):
        return 'Array(is_cell={}, rows={})'.format(self.is_cell, self.rows)


    def __str__(self):
        if self.is_cell:
            if self.rows:
                return '{{cell array: [ {} ]}}'.format(_str_format_rowlist(self.rows))
            else:
                return '{cell array: []}'
        else:
            if self.rows:
                return '{{array: [ {} ]}}'.format(_str_format_rowlist(self.rows))
            else:
                return '{array: [] }'


#
# Handles
#
# Function handles could potentially be considered a subclass of Primitive,
# because they're basically literal values, but they have an implication of
# being closures and thus callers might want to treat them differently than
# Primitive objects.  Anonymous functions are not a Primitive or Reference
# subclass because they are closures, because they're not simple literal
# values, and because they don't have names.

class Handle(Entity):
    pass


class FunHandle(Handle):
    _attr_names = ['name']
    _visitable_attr = ['name']

    def __repr__(self):
        return 'FunHandle(name={})'.format(repr(self.name))

    def __str__(self):
        return '{{function @ handle: {}}}'.format(_str_format(self.name))


class AnonFun(Handle):
    _attr_names = ['args', 'body']
    _visitable_attr = ['args', 'body']

    def __repr__(self):
        return 'AnonFun(args={}, body={})'.format(repr(self.args), repr(self.body))

    def __str__(self):
        return '{{anon @ handle: args {} body {} }}'.format(_str_format_args(self.args),
                                                            _str_format(self.body))


#
# References.
#
# When it's impossible to determine whether a reference is to an array or
# a function, the Reference object will not be of a more specific subtype.
# If something can be determined to be, say, an ArrayReference, that's the
# type it will have.

class Reference(Entity):
    # Default field is a name.
    _attr_names = ['name']


class Identifier(Reference):
    '''Identifiers NOT used in the syntactic context of a function call or
    array reference.  The value they represent may still be an array or
    function, but where we encountered it, we did not see it used in the
    manner of an array reference or functon call.'''

    _attr_names = ['name']

    def __repr__(self):
        return 'Identifier(name={})'.format(repr(self.name))

    def __str__(self):
        return '{{identifier: "{}"}}'.format(self.name)


class ArrayOrFunCall(Reference):
    '''Syntactically looks like either an array reference or a function call.'''

    _attr_names = ['name', 'args']
    _visitable_attr = ['name', 'args']

    def __repr__(self):
        return 'ArrayOrFunCall(name={}, args={})'.format(repr(self.name),
                                                         repr(self.args))

    def __str__(self):
        return '{{function/array: {} {}}}'.format(_str_format(self.name),
                                                  _str_format_args(self.args))


class FunCall(Reference):
    '''Objects that are determined to be function calls.'''

    _attr_names = ['name', 'args']
    _visitable_attr = ['name', 'args']

    def __repr__(self):
        return 'FunCall(name={}, args={})'.format(repr(self.name),
                                                  repr(self.args))

    def __str__(self):
        return '{{function {} {} }}'.format(_str_format(self.name),
                                            _str_format_args(self.args))


class ArrayRef(Reference):
    '''Objects that are determined to be array references.
    The field `is_cell` is True if this is a cell array.'''

    _attr_names = ['name', 'args', 'is_cell']
    _visitable_attr = ['name', 'args']

    def __repr__(self):
        return 'ArrayRef(is_cell={}, name={}, args={})'.format(self.is_cell,
                                                               repr(self.name),
                                                               repr(self.args))

    def __str__(self):
        if self.is_cell:
            if self.args:
                return '{{cell array: {} [ {} ]}}'.format(_str_format(self.name),
                                                          _str_format_subscripts(self.args))
            else:
                return '{{cell array: {} []}}'.format(_str_format(self.name))
        else:
            if self.args:
                return '{{array {}: [ {} ]}}'.format(_str_format(self.name),
                                                     _str_format_subscripts(self.args))
            else:
                return '{{array {}: [] }}'.format(_str_format(self.name))


class StructRef(Reference):
    '''Objects that are determined to be structure references.
    Warning: `name` may be an expression, not just an identifier.'''

    _attr_names = ['name', 'field', 'dynamic']
    _visitable_attr = ['name', 'field']

    def __repr__(self):
        return 'StructRef(name={}, field={}, dynamic_access={})'.format(
            repr(self.name), repr(self.field), repr(self.dynamic))

    def __str__(self):
        return '{{struct: {}.{} using {} access}}'.format(
            _str_format(self.name), _str_format(self.field),
            'dynamic' if self.dynamic else 'static')


# Operators
# .........................................................................

class Operator(Expression):
    '''Parent class for operators in expressions.'''
    pass


class UnaryOp(Operator):
    _attr_names = ['op', 'operand']
    _visitable_attr = ['operand']

    def __repr__(self):
        return 'UnaryOp(op=\'{}\', operand={})'.format(
            self.op, repr(self.operand))

    def __str__(self):
        return '{{unary op expression {} operand {}}}'.format(
            self.op, _str_format(self.operand))


class BinaryOp(Operator):
    _attr_names = ['op', 'left', 'right']
    _visitable_attr = ['left', 'right']

    def __repr__(self):
        return 'BinaryOp(op=\'{}\', left={}, right={})'.format(
            self.op, repr(self.left), repr(self.right))


    def __str__(self):
        return '{{binary op expression {} left {} right {}}}'.format(
            self.op, _str_format(self.left), _str_format(self.right))


class ColonOp(Operator):
    _attr_names = ['left', 'middle', 'right']
    _visitable_attr = ['left', 'middle', 'right']

    def __repr__(self):
        return 'ColonOp(left={}, middle={}, right={})'.format(
            repr(self.left), repr(self.middle), repr(self.right))

    def __str__(self):
        return '{{colon op expression: left={}, middle={}, right={}}}'.format(
            _str_format(self.left), _str_format(self.middle), _str_format(self.right))


class Transpose(Operator):
    _attr_names = ['op', 'operand']
    _visitable_attr = ['operand']

    def __repr__(self):
        return 'Transpose(op=\'{}\', operand={})'.format(
            self.op, repr(self.operand))

    def __str__(self):
        return '{{transpose expression: {} operator {} }}'.format(
            _str_format(self.operand), self.op)


# Definitions: assignments, function definitions, scripts.
# .........................................................................

class Definition(MatlabNode):
    '''Parent class for definitions.'''
    pass


class ScopeDecl(Definition):
    _attr_names = ['type', 'variables']
    _visitable_attr = ['variables']

    def __repr__(self):
        return 'ScopeDecl(type={}, variables={})'.format(repr(self.type),
                                                         repr(self.variables))

    def __str__(self):
        return '{{scope: {} {}}}'.format(self.type, _str_format(self.variables))


class Assignment(Definition):
    _attr_names = ['lhs', 'rhs']
    _visitable_attr = ['lhs', 'rhs']

    def __repr__(self):
        return 'Assignment(lhs={}, rhs={})'.format(repr(self.lhs), repr(self.rhs))

    def __str__(self):
        return '{{assign: {} = {}}}'.format(_str_format(self.lhs),
                                            _str_format(self.rhs))


class FunDef(Definition):
    _attr_names = ['name', 'parameters', 'output', 'body', 'context']
    _visitable_attr = ['name', 'parameters', 'output', 'body']

    def __repr__(self):
        return 'FunDef(name={}, parameters={}, output={}, body={})'.format(
            repr(self.name), repr(self.parameters), repr(self.output), repr(self.body))

    def __str__(self):
        # This conditonal is only here because the old format didn't print
        # parentheses around the output if the output was a single thing (i.e.,
        # not a list).
        if self.output:
            if len(self.output) > 1:
                output = '[ ' + _str_format_subscripts(self.output) + ' ]'
            else:
                output = _str_format(self.output[0])
        else:
            output = 'none'
        if self.parameters:
            params = _str_format_args(self.parameters)
        else:
            params = '( none )'
        return '{{function definition: {} parameters {} output {} body {}}}'.format(
            _str_format(self.name), params, output, _str_format(self.body))


# Decided not to do this for now.

# class Script(Definition):
#     _attr_names = ['name', 'body']



# Flow control.
# .........................................................................

class FlowControl(MatlabNode):
    pass
    # FIXME


class TryCatch(FlowControl):
    _attr_names = ['body', 'catch_var', 'catch_body']
    _visitable_attr = ['body', 'catch_var', 'catch_body']

    def __repr__(self):
        return 'Try(body={}, catch_var={}, catch_body={})'.format(
            repr(self.body), repr(self.catch_var), repr(self.catch_body))

    def __str__(self):
        return '{{try: {} catch_var {} catch_body {}}}'.format(
            _str_format(self.body), _str_format(self.catch_var),
            _str_format(self.catch_body))


class Switch(FlowControl):
    _attr_names = ['cond', 'case_tuples', 'otherwise']
    _visitable_attr = ['cond', 'case_tuples', 'otherwise']

    def __repr__(self):
        return 'Switch(cond={}, case_tuples={}, otherwise={})'.format(
            repr(self.cond), repr(self.case_tuples), repr(self.otherwise))

    def __str__(self):
        return '{{switch stmt: {} case_tuples {} otherwise {}}}'.format(
            _str_format(self.cond), _str_format(self.case_tuples),
            _str_format(self.otherwise))


class If(FlowControl):
    _attr_names = ['cond', 'body', 'elseif_tuples', 'else_body']
    _visitable_attr = ['cond', 'body', 'elseif_tuples', 'else_body']

    def __repr__(self):
        return 'If(cond={}, body={}, elseif_tuples={}, else={})'.format(
            repr(self.cond), repr(self.body), repr(self.elseif_tuples),
            repr(self.else_body))

    def __str__(self):
        return '{{if stmt: {} body {} elseif_tuples {} else {}}}'.format(
            _str_format(self.cond), _str_format(self.body),
            _str_format(self.elseif_tuples), _str_format(self.else_body))


class While(FlowControl):
    _attr_names = ['cond', 'body']
    _visitable_attr = ['cond', 'body']

    def __repr__(self):
        return 'While(cond={}, body={})'.format(repr(self.cond), repr(self.body))

    def __str__(self):
        return '{{while stmt: condition {} body {}}}'.format(
            _str_format(self.cond), _str_format(self.body))


class For(FlowControl):
    _attr_names = ['var', 'expr', 'body']
    _visitable_attr = ['var', 'expr', 'body']

    def __repr__(self):
        return 'For(var={}, expr={}, body={})'.format(repr(self.var),
                                                      repr(self.expr),
                                                      repr(self.body))

    def __str__(self):
        return '{{for stmt: var {} in {} do {}}}'.format(_str_format(self.var),
                                                         _str_format(self.expr),
                                                         _str_format(self.body))


class Branch(FlowControl):
    __attr_names = ['kind']

    def __str__(self):
        if self.kind == 'break':
            return '{break}'
        elif self.kind == 'continue':
            return '{continue}'
        elif self.kind == 'return':
            return '{return}'


# Shell commands.
# .........................................................................

class ShellCommand(MatlabNode):
    _attr_names = ['command', 'background']

    def __repr__(self):
        return 'ShellCommand(command={}, bkgnd={})'.format(repr(self.command),
                                                           self.background)

    def __str__(self):
        bkgnd = ' &' if self.background else ''
        return '{{shell command: {}{}}}'.format(_str_format(self.command), bkgnd)


# Comments.
# .........................................................................

class Comment(MatlabNode):
    _attr_names = ['content']

    def __repr__(self):
        return 'Comment(content={})'.format(repr(self.content))

    def __str__(self):
        return '{{comment: {}}}'.format(self.content)



# Visitor.
# .........................................................................
# This is a mostly standard Python-style Visitor Pattern, except that it
# designed to work with both individual MatlabNode objects and lists of
# MatlabNodes.
#
# This automatically visits the subcomponents of nodes such as the arguments
# to function calls, so the caller does not have to include that logic.  It
# assumes callers return a node if a node is to be transformed (such as
# changed from one node class to another).  This does depth-first traversal.

class MatlabNodeVisitor(object):
    def visit(self, node):
        if isinstance(node, list):
            meth = getattr(self, 'visit_list', None)
            if meth is None:
                meth = self.default_visit_list
            return meth(node)
        elif isinstance(node, tuple):
            return (self.visit(node[0]), self.visit(node[1]))
        else:
            # Call ourselves on the node attributes that are indicated as
            # being ones that should be visited recursively.
            for a in type(node)._visitable_attr:
                value = getattr(node, a, None)
                if value:
                    setattr(node, a, self.visit(value))

            # Now call user's visitor methods and return the final result.
            methname = 'visit_' + type(node).__name__
            meth = getattr(self, methname, None)
            if meth is None:
                meth = self.default_visit
            return meth(node)


    def default_visit(self, node):
        '''Default visitor.  Users can redefine this if desired.'''
        return node


    def default_visit_list(self, node):
        '''Default visitor for lists.  Users can redefine this if desired.'''
        return [self.visit(item) for item in node]


# General helpers.
# .........................................................................

def _str_format(thing, no_parens=False):
    if isinstance(thing, list):
        formatted = ' '.join([_str_format(item) for item in thing])
        if no_parens:
            return formatted
        else:
            return '( ' + formatted + ' )'
    else:
        return str(thing)


def _str_format_args(thing):
    if isinstance(thing, list):
        return '( ' + ', '.join([_str_format(item) for item in thing]) + ' )'
    else:
        return str(thing)


def _str_format_subscripts(subscripts):
    return ', '.join([_str_format(thing) for thing in subscripts])


def _str_format_rowlist(rows):
    last = len(rows) - 1
    i = 1
    text = ''
    for row in rows:
        text += '{{row {}: {}}}'.format(i, _str_format_subscripts(row))
        if i <= last:
            text += '; '
        i += 1
    return text
