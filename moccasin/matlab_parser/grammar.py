#!/usr/bin/env python
#
# @file    grammar.py
# @brief   Core of the MATLAB grammar definition in PyParsing
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

# Basic principles of the parser
# ------------------------------
#
# The main entry point are the functions `MatlabGrammar.parse_string()` and
# `MatlabGrammar.parse_file()`.  There are a few other public methods on the
# class `MatlabGrammar` for debugging and other tasks, but the basic goal of
# `MatlabGrammar` is to provide the two main entry points.  Both of those
# functions return a data structure that a caller can examine to determine
# what was found in a given MATLAB input string or file.
#
# The data structure returned by the parsing functions is an object of class
# `MatlabContext`.  This object contains a number of fields designed for
# convenient processing by the rest of the MOCCASIN toolchain.  The
# representation of the MATLAB input itself is stored in a field called
# `nodes` inside the `MatlabContext` object.  This field consists of a list
# of `MatlabNode` objects.  They are described below.
#
# Loosely speaking, each `MatlabNode` object represents a MATLAB statement,
# in the order they were read from the input file or string.  The
# `MatlabNode` objects are close to being an Abstract Syntax Tree (AST)
# representation of the input; the main difference is that the nodes capture
# more than only the syntax.
#
# A difficult problem with interpreting MATLAB is that the function call
# forms that use parentheses look identical to matrix/array accesses, and in
# fact, in MATLAB there's no way to tell them apart on the basis of syntax
# alone.  A program must determine whether the first name is a function or
# command, which means it's ultimately run-time dependent and depends on the
# functions and scripts that the user has defined.  However, as mentioned
# above, one of the core goals of MOCCASIN is to be able to run independently
# of the user's environment (and indeed, without using MATLAB at all): in
# other words, _MOCCASIN does not have access to the user's MATLAB
# environment_, so it must resort to various heuristics to try to guess
# whether a given entity is meant to be an array reference or a function
# call.  It often cannot, and then it can only return `Ambiguous` as a
# way to indicate it could be either one.
#
# Hierarchy of `MatlabNode` object classes
# ----------------------------------------
#
# There are numerous `MatlabNode` objects and they are hierarchically
# organized as depicted by the following tree diagram.
#
# MatlabNode
# |
# +-Expression
# |  +- Entity
# |  |  +- Primitive
# |  |  |  +- Number
# |  |  |  +- String
# |  |  |  `- Special       # A colon or tilde character, or the string "end".
# |  |  |
# |  |  +- Array            # Unnamed arrays ("square-bracket" type or cell).
# |  |  |
# |  |  +- Handle
# |  |  |  +- FuncHandle    # A function handle, e.g., "@foo"
# |  |  |  `- AnonFun       # An anonymous function, e.g., "@(x,y)x+y".
# |  |  |
# |  |  `- Reference        # Objects that store or return values.
# |  |     +- Identifier
# |  |     +- FunCall
# |  |     +- ArrayRef
# |  |     +- StructRef
# |  |     `- Ambiguous
# |  |
# |  `- Operator
# |     +- UnaryOp
# |     +- BinaryOp
# |     +- ColonOp
# |     `- Transpose
# |
# +--Definition
# |  +- FunDef
# |  +- Assignment
# |  `- ScopeDecl
# |
# +--FlowControl
# |  +- If
# |  +- While
# |  +- For
# |  +- Switch
# |  +- Try
# |  `- Branch
# |
# +--ShellCommand
# |
# `- Comment
#
# Roughly speaking, the scheme of things is as follows:
#
# * `Expression` is the parent class of entities and operators that are the
#   constituents of formulas.  They can appear in many places: in variable
#   assignments, arguments of functions, value tests in `case` statements
#   within `switch`, and so on.  Worth noting is the fact that the parser
#   never produces `Expression` objects per se; it produces a more specific
#   class of object such as a number or a binary operator expression.
#
# * `Entity` objects represent things that go into `Expression` contents or
#   other places where expressions are used.  There are a number of
#   subclasses under `Entity`:
#
#   - `Primitive` objects are simple literal values.
#
#   - `Array` objects are also literal values, but are structured.  `Array`
#      objects may be regular arrays or cell arrays.  In this parser, both
#      types of arrays are treated essentially identically, with only a
#      Boolean attribute (`is_cell`) in `Array` to distinguish them.
#
#   - `Handle` objects in some ways are similar to `Primitive` objects and in
#      other ways similar to `Reference`.  They have an implication of being
#      closures, and consequently may need to be treated specially, so they
#      are grouped into their own subclass.
#
#   - `Reference` objects point to values.  This subclass includes simple
#      variables as well as more complex entities, such as named arrays.
#      Unfortunately, they are among the most difficult objects to classify
#      correctly in MATLAB.  The most notable case involves array accesses
#      versus function calls, which are syntactically identical in MATLAB.
#      `Ambiguous` objects represent something that cannot be
#      distinguished as either an array reference or a named function call.
#      This problem is discussed in a separate section below.  If the parser
#      *can* infer that a given term is an array reference or a function
#      call, then it will report them as `ArrayRef` or `FunCall`,
#      respectively, but often it is impossible to tell and the parser must
#      resort to using `Ambiguous`.
#
# * `Operator` objects are recursive tree-structured combinations of
#   operators and `Entity` objects.  Operators generally have an attribute
#   that represents the specific operation (e.g., `+` or `./`), and operands.
#   Depending on the operator, there may be one or more operands.
#
# * `Definition` objects define `Reference` objects.
#
# * `FlowControl` objects represent constructs with conditions and bodies.
#   These are the classic flow control constructs such as
#   `if`-`then`-`else`. The bodies of these objects contain lists of
#   statements that may contain any of the other types of objects, including
#   other `FlowControl` type objects.
#
# * `ShellCommand` objects represent (as you may have guessed) MATLAB shell
#   command statements.
#
# * `Comment` objects represent inline or block comments.
#
# Working with MatlabNode objects
# -------------------------------
#
# Some examples will hopefully provide a better sense for how the
# representation works.  Suppose we have an input file containing this:
#
#  a = 1
#
# `MatlabGrammar.parse_file()` will return a `MatlabContext` object after
# parsing this, and this context object will have one attribute, `nodes`,
# containing a list of `MatlabNode` objects.  In the present case, that list
# will have a length of 1 because there is only one line in the input.  Here
# is what the list will look like:
#
#  [ Assignment(lhs=Identifier(name='a'), rhs=Number(value='1')) ]
#
# The `Assignment` object has two attributes, `lhs` and `rhs`, representing
# the left-hand and right-hand sides of the assignment, respectively.  Each
# of test attribute values is another `MatlabNode` object.  The object
# representing the variable `a` is
#
#  Identifier(name='a')
#
# This object class has just one attribute, `name`, which can be accessed
# directly to get the value.  Here is an example of how you might do this by
# typing some commands in an interactive Python interpreter:
#
#  (Pdb) x = Identifier(name='a')
#  (Pdb) x.name
#  'a'
#
# Here is another example.  Suppose the input file contains the following:
#
#  a = [1 2]
#
# The parser will return the following node structure:
#
#  [
#  Assignment(lhs=Identifier(name='a'),
#             rhs=Array(is_cell=False,
#                       rows=[[Number(value='1'), Number(value='2')]]))
#  ]
#
# The `Array` object has an attribute, `rows`, that stores the rows of the
# array contents as a list of lists.  Each list inside the outermost list
# represents a row.  Thus, in this simple case where there is only one row,
# the value of the `rows` attribute consists of a list containing one list,
# and this one lists contains the representations for the numbers `1` and `2`
# used in the array expression.
#
# Some other types of `MatlabNode` objects have lists of nodes within them.
# For instance, `While` contains an expression in the attribute `cond` and a
# list of nodes in the attribute `body`.  This list of nodes can contain any
# statement that can appear in the body of a MATLAB `while`, such as
# assignments, other flow-control statements, function calls, or just
# primitive entities or identifiers.
#
# And those are the basics.  A caller can take the list of nodes turned by
# the parser and walk down the list one by one, doing whatever processing is
# appropriate for the caller's purposes.  Each time it encounters a
# `MatlabNode` object, it can extract information and process it.  The fact
# that everything is rooted in `MatlabNode` means that callers can use the
# *Visitor* pattern to implement processing algorithms.
#
# Matrices and functions in MATLAB
# --------------------------------
#
# As mentioned above, an array access such as `foo(1, 2)` or `foo(x)` looks
# syntactically identical to a function call in MATLAB.  This poses a problem
# for the MOCCASIN parser: in many situations it can't tell if something is
# an array or a function, so it can't properly label the object in the
# parsing results.  (It is worth keeping in mind at this point that MOCCASIN
# does not have access to the user's MATLAB environment.)
#
# The way MOCCASIN approaches this problem is the following:
#
# 1. If it can determine unambiguously that something must be an array access
#    based on how it is used syntactically, then it will make it an object of
#    class `ArrayRef`.  Specifically, this is the case when an array access
#    appears on the left-hand side of an assignment statement, as well as in
#    other situations when the access uses a bare colon character (`:`) for a
#    subscript (because bare colons cannot be used as an argument to a
#    function call).
#
# 2. If it can _infer_ that an object is most likely an array access, it will
#    again make it an `ArrayRef` object.  MOCCASIN does simple type inference
#    by remembering variables it has seen used in assignments.  When those
#    are used in other expressions, MOCCASIN can infer they must be variable
#    names and not function names.
#
# 3. Internally, MOCCASIN has a predefined list of known MATLAB functions and
#    commands.  (The list is stored in the file `functions.py` and was
#    generated by inspecting the MATLAB documentation for the 2014b version
#    of MATLAB.)  If an ambiguous array reference or function call has a name
#    that appears on this list, it is inferred to be a `FunCall` and not an
#    `ArrayRef`.
#
# 4. In all other cases, it will label the object `Ambiguous`.
#
# Users will need to do their own processing when they encounter a
# `Ambiguous` object to determine what kind of thing the object really is.
# In the most general case, MOCCASIN can't tell from syntax alone whether
# something could be a function, because without running MATLAB (and running
# it _in the user's environment_, because the user's environment affects the
# functions and scripts that MATLAB knows about), it simply cannot know.
#
# Expressions
# -----------
#
# MATLAB's mathematical notation is in infix format; MOCCASIN turns this into
# a Abstract Syntax Tree (AST) in which `Operator` objects are middle nodes
# and leaves are either `Entity` or other `Operator` objects (which in turn
# can have further child objects).  There is an `Entity` parent class for
# different types of primitive and other entities that have values, and there
# is an `Operator` parent class for operators with four classes of operators
# within that.
#
# Rather than always return some sort of single container object for all
# expressions, the MOCCASIN parser returns the simplest representation it can
# produce.  What this means is that if a given MATLAB input expression (for
# example, the right-hand side of some variable assignment) consists of
# simply a number or string, then MOCCASIN will return that entity directly:
# it will be a `Number` or `String`.  This is true in contexts where an
# expression is naturally expected, as well as contexts such as function
# bodies where statements are expected.  (An expression appear as a statement
# in MATLAB simply results in MATLAB printing the evaluated value of the
# expression.)
#
# Here is an example.  Suppose that an input consists of this:
#
#  if x > 1
#      foo = 5
#  end
#
# The MOCCASIN parser will return the following (with indentation added here
# to improve readability):
#
#  [
#  If(cond=BinaryOp(op='>', left=Identifier(name='x'), right=Number(value='1')),
#     body=[ Assignment(lhs=Identifier(name='foo'), rhs=Number(value='5')) ],
#     elseif_tuples=[],
#     else=None)
#  ]
#
# A MATLAB `if` statements's condition is an expression, and here the
# attribute `cond` contains the expression `BinaryOp(op='>',
# left=Identifier(name='x'), right=Number(value='1')`.  The body of the input
# consists of a single assignment statement.  MOCCASIN stores this as `body`
# in the `If` object instance; the value of `body` is always a list but in
# this case it contains only a single object, `Assignment`.  The right-hand
# side of the assignment is an expression consisting of a single value, which
# MOCCASIN represents directly as the value.
#
# Callers can use the class hierarchy to determine what kind of objects they
# receive.  The Python `isinstance` operator is particular useful for this
# task.  For instance, for some object `thing`, the test `isinstance(thing,
# Primitive)` would reveal if the object is a simple value that needs no
# further evaluation.
#
# Special cases
# -------------
#
# Most of what the parser returns is either an object or a list of objects.
# There are two constructs that deviate from this pattern: the `elseif` terms
# of an `if`-`elseif` series of MATLAB statements, and the `case` parts of
# `switch` statements.  Both of these involve one or more pairs of condition
# expressions and an accompanying list of statements.  The MOCCASIN parser
# represents these using lists of Python tuples of the form (_condition_,
# _list of statements_).  The relevant attributes storing these lists of
# tuples on `If` and `Switch` objects are `elseif_tuples` for the former and
# `case_tuples` for the latter.
#
# A different kind of special case involves `StructRef`, used to store MATLAB
# structure references.  In MATLAB, the fields of `struct` entities can be
# named statically or dynamically; the latter is known as _dynamic field
# references_.  Syntactically, this takes the form of a parenthesized field
# reference such as `somestruct.(var)`, and MATLAB evaluates the expression
# in the parentheses (in this case, `var`) to obtain the name of the field.
# However, in MOCCASIN, a field name is represented as an `Identifier`
# object, the same as the name of a variable would be.  In order for callers
# to be able to tell whether a given structure field reference is a literal
# value ("the field name is `x`") or something that is to be evaluated to get
# the value ("the field name is stored in `x`"), MOCCASIN provides a Boolean
# attribute on `StructRef` named `dynamic_access`.  Its value is `True` if
# the `StructRef` attribute `field` is something that is meant to be
# evaluated.
#

# Preface material.
# .............................................................................

from __future__ import print_function
import codecs
import copy
import pdb
import six
import sys
import traceback
import pyparsing                        # Need this for version check, so ...
from pyparsing import *                 # ... DON'T merge this & previous stmt!
from distutils.version import LooseVersion
from collections import defaultdict
try:
    from grammar_utils import *
    from context import *
    from matlab import *
    from functions import *
except:
    from .grammar_utils import *
    from .context import *
    from .matlab import *
    from .functions import *

# Check minimum version of PyParsing.

if LooseVersion(pyparsing.__version__) < LooseVersion('2.0.3'):
    raise Exception('MatlabGrammar requires PyParsing version 2.0.3 or higher')

# Necessary optimization.  Without this, the PyParsing grammar defined below
# never finishes parsing anything.

ParserElement.enablePackrat()

# The inefficient nature of this parser leads to easily exceeding the default
# recursion stack limit.  Let's increase it:

sys.setrecursionlimit(5000)



# Exception classes
# .............................................................................

class MatlabParsingException(Exception):
    pass


class MatlabInternalException(Exception):
    pass



# Helper classes
# .............................................................................

# ParseResultsTransformer
#
# Helper class to transform ParseResults to MatlabNode-based output format.
#
# This takes our heavily-annotated output from PyParsing and converts it
# to a tree-based representation consisting of lists of MatlabNode objects.
#
# In what follows, the visit_* functions are visitors named after the names
# of our grammar objects (in the PyParsing grammar definition later below).
# They are named such that the visit() function can dispatch on the name we
# assign to PyParsing objects.  For instance, to format what we label an
# "assignment" in the PyParsing grammar above, there's a function called
# visit_assignment() below.
#
# I would implement this using an annotation-based approach like the
# @dispatch.on and @visit.when annotations that are floating around on the
# net, but can't: the objects we're processing are always ParseResults (a
# single class), so the class-based @visit.when dispatching won't work here.

class ParseResultsTransformer:
    def __init__(self, parser):
        self._parser = parser


    def visit(self, pr):
        if not isinstance(pr, ParseResults):
            # It's a terminal element, so we don't do anything more.
            return pr

        length = len(pr)
        if length > 1 and empty_dict(pr):
            # It's an expression.  We deconstruct the infix notation.
            if pr[1].get('transpose'):
                # Process the first part and revisit the rest, in case we
                # have more than one operator applied to the lead item.
                return self.visit_transpose(pr)
            elif len(pr) == 2 and 'unary operator' in pr[0].keys():
                return self.visit_unary_operator(pr)
            elif len(pr) == 3:
                if 'binary operator' in pr[1].keys():
                    return self.visit_binary_operator(pr)
                elif 'colon operator' in pr[1].keys():
                    return self.visit_colon_operator(pr)
            elif len(pr) == 5 and 'colon operator' in pr[1].keys():
                return self.visit_colon_operator(pr)
            else:
                # This should not happen, but maybe someday it will.
                msg = 'Unexpected expression form encountered in ParseResults.'
                raise MatlabInternalException(msg)

        elif length == 1 and pr[0] == '':
            # An empty string.  This special case handling shoudn't be
            # needed, but for some reason, empty strings don't get tagged
            # with the 'string' key like non-empty strings do.
            return String(value='')

        # Not an expression, but an individual, single parse result.
        # We dispatch to the appropriate transformer by building the name.
        if num_keys(pr) > 1:
            # Sanity check.  This should not happen, but maybe someday it will.
            msg = 'Internal grammar inconsistency: multiple tags for same construct.'
            raise MatlabInternalException(msg)
        key = first_key(pr)
        methname = 'visit_' + '_'.join(key.split())
        meth = getattr(self, methname, None)
        if meth is None:
            return pr
        else:
            return meth(pr)


    def visit_identifier(self, pr):
        return Identifier(name=pr['identifier'])


    def visit_number(self, pr):
        return Number(value=pr['number'])


    def visit_string(self, pr):
        return String(value=pr['string'])


    def visit_tilde(self, pr):
        return Special(value='~')


    def visit_colon(self, pr):
        return Special(value=':')


    def visit_end_operator(self, pr):
        return Special(value='end')


    def visit_unary_operator(self, pr):
        op_key = first_key(pr[0])
        op = pr[0][op_key]
        operand = self.visit(pr[1])
        if op == '-' and isinstance(operand, Number):
            # Replace [UnaryOp(op='-'), Number(value='x')] with Number(value='-x')
            # But watch out if it's already a negative number.
            if operand.value.startswith('-'):
                return Number(value=operand.value[1:])
            else:
                return Number(value=op + operand.value)
        elif op == '+' and isinstance(operand, Number):
            # Doesn't seem worth preserving the '+'.
            # Replace [UnaryOp(op='+'), Number(value='x')] with Number(value='x')
            return Number(operand.value)
        else:
            # This is probably negation, "~".
            return UnaryOp(op=op, operand=operand)


    def visit_binary_operator(self, pr):
        op_key = first_key(pr[1])
        op = pr[1][op_key]
        left = self.visit(pr[0])
        right = self.visit(pr[2])
        return BinaryOp(op=op, left=left, right=right)


    def visit_colon_operator(self, pr):
        if len(pr) == 3:
            left=self.visit(pr[0])
            middle=None
            right=self.visit(pr[2])
        elif len(pr) == 5:
            left=self.visit(pr[0])
            middle=self.visit(pr[2])
            right=self.visit(pr[4])
        return ColonOp(left=left, middle=middle, right=right)


    def visit_transpose(self, pr):
        operand=self.visit(pr[0])
        op = pr[1]['transpose']
        return Transpose(op=op, operand=operand)


    def visit_standalone_expression(self, pr):
        content = pr['standalone expression']
        return self.visit(content)


    def visit_assignment(self, pr):
        content = pr['assignment']
        lvalue = self.visit(content['lhs'])
        rvalue = self.visit(content['rhs'])
        node = Assignment(lhs=lvalue, rhs=rvalue)
        return node


    def visit_array(self, pr):
        content = pr['array']
        # Two kinds of array situations: a bare array, and one where we
        # managed to determine it's an array access (and not the more
        # ambiguous function call or array access).  If we have an 'array
        # base' part, it's the latter; if we have a row list, it's the former.
        if 'array base' in content:
            base = content['array base']
            if 'name' in base:
                name = self.visit(base['name'])
            else:
                name = self.visit(base)
            subscripts = self._convert_list(content['subscript list'])
            return ArrayRef(name=name, args=subscripts, is_cell=False)
        elif 'row list' in content:
            # Bare array.
            return Array(rows=self._convert_rows(content['row list']), is_cell=False)
        else:
            # No row list or subscript list => empty array.
            return Array(rows=[], is_cell=False)


    def visit_cell_array(self, pr):
        content = pr['cell array']
        # Two kinds of situations: a bare cell array, and one where we
        # managed to determine it's an array access.  If we have 'row list'
        # in the keys, it's the former.
        if 'row list' in content:
            # Bare array.
            return Array(rows=self._convert_rows(content['row list']), is_cell=True)
        elif 'cell array' in content:
            # Nested reference.
            base = self.visit(content['cell array'])
            subscripts = self._convert_list(content['subscript list'])
            return ArrayRef(name=base, args=subscripts, is_cell=True)
        elif 'name' in content:
            # Basic array reference.
            name = self.visit(content['name'])
            subscripts = self._convert_list(content['subscript list'])
            return ArrayRef(name=name, args=subscripts, is_cell=True)
        else:
            # No row list or subscript list => empty array.
            return Array(rows=[], is_cell=True)


    def visit_array_or_function(self, pr):
        content = pr['array or function']
        the_name = self.visit(content['name'])
        if 'argument list' in content.keys():
            the_args = self._convert_list(content['argument list'])
        else:
            the_args = []
        return Ambiguous(name=the_name, args=the_args)


    def visit_function_handle(self, pr):
        content = pr['function handle']
        if 'name' in content:
            return FuncHandle(name=self.visit(content['name']))
        else:
            if 'parameter list' in content.keys():
                the_args = self._convert_list(content['parameter list'])
            else:
                the_args = []
            the_body = self.visit(content['function definition'])
            return AnonFun(args=the_args, body=the_body)


    def visit_function_definition(self, pr):
        # Processing function definitions requires extra work.  MATLAB
        # functions establish contexts for other constructs and we need to
        # build a dynamic stack to track those contexts.  This is done here
        # by pushing a context object before we process the function
        # definition body, so that the constructs in the body are processed
        # in the appropriate context.

        content = pr['function definition']
        name = self.visit(content['name'])

        params = None
        output = None
        if 'parameter list' in content:
            params = self._convert_list(content['parameter list'])
        if 'output list' in content:
            output = self._convert_list(content['output list'])

        # Chicken, meet egg.  So: create an incomplete FunDef, use it to
        # create a context object, and then set the FunDef's context field.
        fundef = FunDef(name=name, parameters=params, output=output,
                        body=None, context=None)
        fundef.context = self._parser._save_function_definition(fundef)
        self._parser._push_context(fundef.context)

        # Now process the body, having set the context.
        body = None
        if 'body' in content:
            body = self._convert_list(content['body'])

        # Go back and complete the function definition object.
        fundef.body = body

        # And finally, pop the context before returning.
        self._parser._pop_context()

        return fundef


    def visit_ambiguous_id(self, pr):
        content = pr['ambiguous id']
        name = content[0]
        return Ambiguous(name=Identifier(name=name), args=None)


    def visit_struct(self, pr):
        content = pr['struct']
        the_base = self.visit(content['struct base'])
        dynamic = 'dynamic field' in content
        if dynamic:
            the_field = self.visit(content['dynamic field'])
        else:
            the_field = self.visit(content['static field'])
        return StructRef(name=the_base, field=the_field, dynamic=dynamic)


    def visit_shell_command(self, pr):
        content = pr['shell command']
        cmd = content[1][0]
        backgrounded = cmd.strip().endswith('&')
        if backgrounded:
            cmd = cmd[:cmd.rfind('&') - 1]
        return ShellCommand(command=cmd, background=backgrounded)


    def visit_command_statement(self, pr):
        content = pr['command statement']
        the_name = self.visit(content['name'])
        the_args = [String(value=x) for x in content['arguments'].asList()]
        return FunCall(name=the_name, args=the_args)


    def visit_comment(self, pr):
        return Comment(content=pr['comment'][0])


    def visit_control_statement(self, pr):
        content = pr['control statement']
        return self.visit(content)


    def visit_while_statement(self, pr):
        content = pr['while statement']
        the_cond = self.visit(content['expression'])
        the_body = None
        if 'body' in content:
            the_body = self._convert_list(content['body'])
        return While(cond=the_cond, body=the_body)


    def visit_if_statement(self, pr):
        content = pr['if statement']
        the_cond = self.visit(content['expression'])
        the_body = None
        the_else_body = None
        elseifs = []
        if 'body' in content:
            the_body = self._convert_list(content['body'])
        if 'else statement' in content and 'body' in content['else statement']:
            the_else_body = self._convert_list(content['else statement']['body'])
        if 'elseif statements' in content:
            # We create tuples of (condition, body) for each elseif clause.
            for clause in content['elseif statements']:
                cond = self.visit(clause['expression'])
                body = None
                if 'body' in clause:
                    body = self._convert_list(clause['body'])
                elseifs.append((cond, body))
        return If(cond=the_cond, body=the_body, elseif_tuples=elseifs,
                  else_body=the_else_body)


    def visit_switch_statement(self, pr):
        content = pr['switch statement']
        the_cond = self.visit(content['expression'])
        the_other = None
        the_cases = []
        if 'case statements' in content:
            # We create tuples of (condition, body) for each elseif clause.
            for clause in content['case statements']:
                cond = self.visit(clause['expression'])
                body = None
                if 'body' in clause:
                    body = self._convert_list(clause['body'])
                the_cases.append((cond, body))
        if 'otherwise statement' in content and 'body' in content['otherwise statement']:
            the_other = self._convert_list(content['otherwise statement']['body'])
        return Switch(cond=the_cond, case_tuples=the_cases, otherwise=the_other)


    def visit_for_statement(self, pr):
        content = pr['for statement']
        the_var = self.visit(content['loop variable'])
        the_expr = self.visit(content['expression'])
        the_body = None
        if 'body' in content:
            the_body = self._convert_list(content['body'])
        # We can convert references to the loop variable.
        the_body = Disambiguator(self, vars=[the_var]).visit(the_body)
        return For(var=the_var, expr=the_expr, body=the_body)


    def visit_try_statement(self, pr):
        content = pr['try statement']
        the_body = None
        the_var = None
        the_catch_body = None
        if 'body' in content:
            the_body = self._convert_list(content['body'])
        if 'catch variable' in content:
            the_var = self.visit(content['catch variable'])
        if 'catch body' in content:
            the_catch_body = self._convert_list(content['catch body'])
            if the_var:
                # We can convert references to the loop variable.
                the_catch_body = Disambiguator(self, vars=[the_var]).visit(the_catch_body)
        return Try(body=the_body, catch_var=the_var, catch_body=the_catch_body)


    def visit_scope_declaration(self, pr):
        content = pr['scope declaration']
        the_type = content['type'][0]
        the_vars = self._convert_list(content['variables list'])
        return ScopeDecl(type=the_type, variables=the_vars)


    def visit_break_statement(self, pr):
        return Branch(kind='break')


    def visit_return_statement(self, pr):
        return Branch(kind='return')


    def visit_continue_statement(self, pr):
        return Branch(kind='continue')


    def _convert_list(self, list):
        return [self.visit(thing) for thing in list]


    def _convert_rows(self, rowlist):
        # MATLAB doesn't keep blank rows.
        nodelist = [self._convert_list(row['subscript list']) for row in rowlist
                    if 'subscript list' in row]
        return [node for node in nodelist if node]



# NodeTransformer
#
# Helper class that walks down a MatlabNode tree and simultaneously performs
# several jobs:
#
#  1) Tries to infer the whether each object it encounters is a variable or
#     a function.
#
#  2) Saves kind information about identifiers and functions it encounters.
#
#  3) Converts certain classes from one type to another. This is used to do
#     things like convert ambiguous cases, like something that could be
#     either a function call or an array reference, to more specific classes
#     of objects if we have figured out what those objects should be.

class NodeTransformer(MatlabNodeVisitor):
    def __init__(self, parser):
        super(NodeTransformer, self).__init__()
        self._parser = parser


    def visit_FunCall(self, node):
        # Process the subcomponents first.
        node.name = self.visit(node.name)
        node.args = self.visit(node.args)
        # Save the call.
        self._parser._save_function_call(node)
        return node


    def visit_FunDef(self, node):
        parser = self._parser
        # Since we know this to be a function, we record its type as such.
        # Make sure to record it in the parent's context -- that's why this
        # is done before a context is pushed in the next step below.
        parser._save_type(node.name, 'function')
        # Push the new function context.  Note that FunDef is unusual in having
        # a node.context property -- other MatlabNodes don't.
        parser._push_context(node.context)
        # Record inferred type info about the input and output parameters.
        # The type info applies *inside* the function.
        for var in filter(lambda x: isinstance(x, Identifier), (node.output or [])):
            # Output parameters are vars inside the context of a function def.
            parser._save_type(var, 'variable')
        if node.parameters:
            # Look at the rest of the file, to see if we can find a call to
            # this function and correlate the arguments with the parameters,
            # to figure out what type they are based on their usage patterns.
            num_param = len(node.parameters)
            context = parser._context
            # Case 1: direct calls to this function.
            calls = parser._get_direct_calls(node.name, context.parent, anywhere=True)
            for arglist in (calls or []):
                if len(arglist) != num_param:
                    continue
                for i in range(0, num_param):
                    arg = arglist[i]
                    param = node.parameters[i]
                    if not isinstance(param, Identifier):
                        continue
                    if isinstance(arg, FuncHandle):
                        parser._save_type(param, 'function')

                    elif (isinstance(arg, Identifier)
                          and parser._get_type(arg, context) == 'function'):
                        parser._save_type(param, 'function')

                    elif (isinstance(arg, FunCall)
                          and isinstance(arg.name, Identifier)
                          and parser._get_type(arg.name, context) == 'function'):
                        parser._save_type(param, 'variable')

                    elif (isinstance(arg, Primitive) or isinstance(arg, Array)
                          or isinstance(arg, Operator)):
                        parser._save_type(param, 'variable')

                    elif (isinstance(arg, Identifier) and
                          parser._get_type(arg, context) == 'variable'):
                        parser._save_type(param, 'variable')

            # Case 2: passing a handle to this funtion as an argument to another.
            calls = parser._get_indirect_calls(node.name, context.parent, anywhere=True)
            # FIXME: this currently only looks for calls involving odeNN
            # functions, but there are probably others we could inspect.
            if any(func.name.startswith('ode') for func in calls.keys()):
                # This function gets passed as a function handle to a MATLAB
                # odeNN function.  This means that the arguments to the current
                # function are variables, and not other functions.
                for param in node.parameters:
                    if isinstance(param, Identifier):
                        parser._save_type(param, 'variable')
        # Make sure to process the body of this function.
        if node.body:
            node.body = self.visit(node.body)
            parser._context.nodes = node.body
        parser._pop_context()
        return node


    def visit_Assignment(self, node):
        # First visit the lhs and rhs.
        node.lhs = self.visit(node.lhs)
        node.rhs = self.visit(node.rhs)

        # Save this assignment.
        parser = self._parser
        parser._save_assignment(node)

        # Record inferred type info about the input and output parameters.
        lhs = node.lhs
        rhs = node.rhs
        if isinstance(lhs, Identifier):
            if (isinstance(rhs, Array) or isinstance(rhs, Primitive)
                  or isinstance(rhs, Operator)):
                # In these cases, the LHS is clearly a variable.
                parser._save_type(lhs, 'variable')
            elif isinstance(rhs, Handle) or isinstance(rhs, AnonFun):
                # Confusing case: RHS is a function, but *this* is a
                # variable.  If this is instead labeled as a function, then
                # it will lead to erroneous results when the variable is used
                # as an argument to a function call elsewhere.
                parser._save_type(lhs, 'variable')
            elif (isinstance(rhs, FunCall) and isinstance(rhs.name, Identifier)
                and rhs.name.name == 'str2func'):
                # Special case: a function is being created using Matlab's
                # str2func(), so in fact, the thing we're assigning to should
                # be considered a function.
                parser._save_type(lhs, 'function')
            elif (isinstance(rhs, FunCall) or isinstance(rhs, ArrayRef)
                  or isinstance(rhs, ArrayRef) or isinstance(rhs, StructRef)):
                # FIXME: this is an assumption.
                parser._save_type(lhs, 'variable')
        elif isinstance(lhs, ArrayRef):
            # A function call can't appear on the LHS of an assignment, so
            # we know that what we have here is a variable, not a function.
            parser._save_type(lhs.name, 'variable')
        elif isinstance(lhs, StructRef) and not lhs.dynamic:
            if (isinstance(rhs, FunCall) and isinstance(rhs.name, Identifier)
                and rhs.name.name == 'str2func'):
                # Special case: a function is being created using Matlab's
                # str2func(), so in fact, the thing we're assigning to should
                # be considered a function.
                parser._save_type(lhs, 'function')
            else:
                parser._save_type(lhs, 'variable')
            if isinstance(lhs.name, Identifier):
                # It's a simple x.y struct reference => x is a variable.
                parser._save_type(lhs.name, 'variable')
        elif isinstance(lhs, Array):
            # A bare array on the LHS.  If symbols appear as subscripts, they
            # cannot be functions.  They could be array references, but it is
            # enough for now to tag them as variables.  Also, there can only
            # be one row of subscripts in an array used on the LHS.
            for item in lhs.rows[0]:
                if isinstance(item, Ambiguous) and item.args == None:
                    parser._save_type(item.name, 'variable')

        return node


    def visit_Ambiguous(self, node):
        # Visit the pieces first.
        node.name = self.visit(node.name)
        node.args = self.visit(node.args)
        # Now analyze the pieces.
        if isinstance(node.name, Identifier) or isinstance(node.name, StructRef):
            thing = node.name
        else:
            # We don't know how to deal with it.
            return node
        parser = self._parser
        context = parser._context
        if parser._get_type(thing, context) == 'variable':
            # The ambiguous identifier has been assigned a value.  If the
            # value is a function handle or an anonymous function, we can
            # recognize this node as a function call and change it accordingly.
            value = parser._get_assignment(thing, context, recursive=True)
            if value and (isinstance(value, Handle) or isinstance(value, AnonFun)):
                if node.args != None:
                    # It's an identifier followed by arguments.  We know it's
                    # not an array or we wouldn't be here, so we're looking at
                    # a function call.
                    the_args = self.visit(node.args)
                    node = FunCall(name=thing, args=the_args)
                    # Save the call in the present context.
                    parser._save_function_call(node)
                else:
                    # There were no arguments at all (e.g., it was "a" rather
                    # than "a()".  We treat it as a variable.  We can
                    # simplify it to the Identifier object that is the name.
                    return node.name
            else:
                # Either it has no value, or the value is not a handle or
                # anon function.
                if node.args == None:
                    # There were no arguments at all (e.g., it was "a" rather
                    # than "a()".  It's a plain identifier, and we can
                    # simplify it to the Identifier object that is the name.
                    return node.name
                else:
                    # It's an ArrayRef.  We can also convert the
                    # args/subscripts.  Also, if it was previously unknown
                    # whether this name is a function or array, it might have
                    # been put in the list of function calls.  Remove it.
                    if thing in context.calls:
                        context.calls.pop(thing)
                    the_args = self.visit(node.args)
                    node = ArrayRef(name=node.name, args=the_args, is_cell=False)
        elif parser._get_type(thing, context) == 'function':
            # This is a known function or command.  We can convert this
            # to a FunCall.  At this time, we also process the arguments,
            # being careful not to change "None" to [].
            the_args = self.visit(node.args) if node.args else node.args
            node = FunCall(name=thing, args=the_args)
            # Save the call in the present context.
            parser._save_function_call(node)
        elif (isinstance(thing, StructRef) and node.args == []):
            # It's something of the form a.b().  This could be an array
            # reference, but in practice, few people put "()" when referring
            # to an array.  So, it's probably a function call.  FIXME: this
            # is an assumption, not a certainty.  We also process the
            # arguments, being careful not to change "None" to [].
            the_args = self.visit(node.args) if node.args else node.args
            node = FunCall(name=thing, args=the_args)
            # Save the call in the present context.
            parser._save_function_call(node)
        else:
            # Although we didn't change the type of this Ambiguous,
            # we may still be able to change some of its arguments.
            # However, be careful not to change "None" to [].
            if node.args:
                node.args = self.visit(node.args)

        return node


    def visit_ArrayRef(self, node):
        # Process the pieces first.
        node.name = self.visit(node.name)
        node.args = self.visit(node.args)
        # Now analyze the pieces.
        if not isinstance(node.name, Identifier):
            return node
        # If we've decided we have an array reference, then the identifier is
        # a variable.  This is useful when we have not seen an assignment and
        # the variable might have come from, e.g., loading a file.
        self._parser._save_type(node.name, 'variable')
        node.args = self.visit(node.args)
        return node


    def visit_StructRef(self, node):
        # Process the pieces first.
        node.name = self.visit(node.name)
        node.field = self.visit(node.field)
        # Now analyze the pieces.
        # If we have a structure reference where the name is a simple id,
        # we can tag the id as a variable.
        if isinstance(node.name, Identifier):
            self._parser._save_type(node.name, 'variable')
        return node



# Disambiguator
#
# Helper class to traverse a node structure and convert cases of Ambiguous
# to other things, when we know about them.

class Disambiguator(MatlabNodeVisitor):
    def __init__(self, parser, vars=[], functions=[]):
        super(Disambiguator, self).__init__()
        self._parser          = parser
        self._known_vars      = vars
        self._known_functions = functions


    def visit_Ambiguous(self, node):
        # Visit the pieces first.
        node.name = self.visit(node.name)
        node.args = self.visit(node.args)
        # Now analyze the pieces.
        if self._known_vars:
            if isinstance(node.name, Identifier) and node.args == None:
                for var in self._known_vars:
                    if var == node.name:
                        # Don't need create new Identifier; just return this.
                        return node.name
        return node



# MatlabGrammar.
# .............................................................................
# The definition of our MATLAB grammar, in PyParsing.
#
# Note: the grammar is written in reverse order, from smallest elements to
# the highest level parsing object, simply because Python interprets the file
# in this order and needs each item defined before it encounters it later.
# However, for readabily, it's probably easiest to start at the last
# definition (which is _matlab_syntax) and read up.

class MatlabGrammar:

    # First, the lowest-level terminal tokens.
    # .........................................................................

    _EOL        = LineEnd().suppress()
    _SOL        = LineStart().suppress()
    _WHITE      = White(ws=' \t').suppress()

    # Note: For MATLAB, we often need to control where line breaks are
    # allowed.  In PyParsing, the whitespace property is attached to term
    # definitions and not to definitions that only combine the terms; i.e.,
    # when using the "^" or "|" operators to combine terms, it doesn't matter
    # if you precede that with setDefaultWhitespaceChars settings.  You have
    # to set the value for the individual term expressions.  That's why some
    # of the following primitives are wrapped with setDefaultWhitespaceChars.

    ParserElement.setDefaultWhitespaceChars(' \t')

    _SEMI       = Literal(';').suppress()
    _COMMA      = Literal(',').suppress()
    _LPAR       = Literal("(").suppress()
    _RPAR       = Literal(")").suppress()
    _LBRACKET   = Literal('[').suppress()
    _RBRACKET   = Literal(']').suppress()
    _LBRACE     = Literal('{').suppress()
    _RBRACE     = Literal('}').suppress()
    _EQUALS     = Literal('=').suppress()
    _DOT        = Literal('.').suppress()
    _ELLIPSIS   = Literal('...')

    ParserElement.setDefaultWhitespaceChars(' \t\n\r')

    # This definition of numbers knowingly ignores imaginary numbers because
    # they're not used in our domain.

    _INTEGER    = Word(nums)
    _EXPONENT   = Combine(oneOf('E e D d') + Optional(oneOf('+ -')) + Word(nums))
    _FLOAT      = (Combine(Word(nums) + Optional('.' + Word(nums)) + _EXPONENT)
                   | Combine(Word(nums) + '.' + _EXPONENT)
                   | Combine(Word(nums) + '.' + Word(nums))
                   | Combine('.' + Word(nums) + _EXPONENT)
                   | Combine('.' + Word(nums))
                   | Combine(Word(nums) + '.'))

    # Next come definitions of terminal elements.  The funky syntax with the
    # second parenthesized argument on each line is something PyParsing allows;
    # it's a short form, equivalent to calling .setResultsName(...).

    _NUMBER     = (_FLOAT | _INTEGER)                 ('number')
    _STRING     = QuotedString("'", escQuote="''")    ('string')

    _TILDE      = Literal('~')                        ('tilde')

    ParserElement.setDefaultWhitespaceChars(' \t')

    _UMINUS     = Literal('-')                        ('unary operator')
    _UPLUS      = Literal('+')                        ('unary operator')
    _UNOT       = Literal('~')                        ('unary operator')
    _TIMES      = Literal('*')                        ('binary operator')
    _ELTIMES    = Literal('.*')                       ('binary operator')
    _MRDIVIDE   = Literal('/')                        ('binary operator')
    _MLDIVIDE   = Literal('\\')                       ('binary operator')
    _RDIVIDE    = Literal('./')                       ('binary operator')
    _LDIVIDE    = Literal('.\\')                      ('binary operator')
    _MPOWER     = Literal('^')                        ('binary operator')
    _ELPOWER    = Literal('.^')                       ('binary operator')
    _PLUS       = Literal('+')                        ('binary operator')
    _MINUS      = Literal('-')                        ('binary operator')
    _LT         = Literal('<')                        ('binary operator')
    _LE         = Literal('<=')                       ('binary operator')
    _GT         = Literal('>')                        ('binary operator')
    _GE         = Literal('>=')                       ('binary operator')
    _EQ         = Literal('==')                       ('binary operator')
    _NE         = Literal('~=')                       ('binary operator')
    _AND        = Literal('&')                        ('binary operator')
    _OR         = Literal('|')                        ('binary operator')
    _SHORT_AND  = Literal('&&')                       ('binary operator')
    _SHORT_OR   = Literal('||')                       ('binary operator')

    # Operators that have special-case handling.

    _COLON      = Literal(':')
    _NC_TRANSP  = Literal(".'")                       ('transpose')
    _CC_TRANSP  = Literal("'")                        ('transpose')

    ParserElement.setDefaultWhitespaceChars(' \t\n\r')

    # Keywords.  This list is based on what the command 'iskeyword' returns
    # in MATLAB 2014b.  Note that 'end' as an operator is defined again below.

    _BREAK      = Keyword('break')
    _CASE       = Keyword('case')
    _CATCH      = Keyword('catch')
    _CLASSDEF   = Keyword('classdef')
    _CONTINUE   = Keyword('continue')
    _ELSE       = Keyword('else')
    _ELSEIF     = Keyword('elseif')
    _END        = Keyword('end')
    _FOR        = Keyword('for')
    _FUNCTION   = Keyword('function')
    _GLOBAL     = Keyword('global')
    _IF         = Keyword('if')
    _OTHERWISE  = Keyword('otherwise')
    _PARFOR     = Keyword('parfor')
    _PERSISTENT = Keyword('persistent')
    _RETURN     = Keyword('return')
    _SPMD       = Keyword('spmd')
    _SWITCH     = Keyword('switch')
    _TRY        = Keyword('try')
    _WHILE      = Keyword('while')

    # Identifiers.
    #
    # _id defines identifiers that can be used in user programs.  They can't
    # be the same as known MATLAB language keywords.  _name defines a labeled
    # version of _id that we use in most grammar expressions below to avoid
    # writing "Group(_id)('name')".

    _reserved   = _BREAK | _CASE | _CATCH | _CLASSDEF | _CONTINUE \
                  | _ELSE | _ELSEIF | _END | _FOR | _FUNCTION \
                  | _GLOBAL | _IF | _OTHERWISE | _PARFOR | _PERSISTENT \
                  | _RETURN | _SPMD | _SWITCH | _TRY | _WHILE

    _identifier = Word(alphas, alphanums + '_')
    _id         = NotAny(_reserved) + _identifier('identifier')
    _name       = Group(_id)('name')

    # Grammar for expressions.
    #
    # Some up-front notes:
    #
    # 1) Calling PyParsing's setResultsName() function or its equivalent
    # yields A COPY of the thing affected -- it does not return the original
    # thing.  This means that if you have a grammar element of the form
    #             _foo = Group(_bar('bar') | _biff('biff'))
    # then _bar and _biff never actually get invoked when _foo is invoked;
    # what get invoked are copies of _bar and _biff, because that's what gets
    # stored in _foo.  This has implications for using parse actions and also
    # debug tracing.  Right now, we no longer use parse actions, but beware
    # that if parse actions are ever attached to _bar & _biff, they are not
    # actually called when _foo is invoked because _foo uses copies of _bar
    # and _biff.  This leads to subtle and frustrating rounds of bug-chasing.
    #
    # 2) The grammar below is sometimes designed with the assumption that the
    # input is valid Matlab.  This fits our purpose, which is to parse valid
    # Matlab, so we can afford to produce something simpler here and assume
    # that the input won't do some things that the Matlab parser would
    # reject.  The basic rule is: accept everything that's valid Matlab, but
    # don't worry about deliberately excluding what isn't valid Matlab.
    # .........................................................................

    _expr          = Forward()
    _expr_in_array = Forward()

    # The possible statement separators/delimiters in Matlab are:
    #   - EOL
    #   - line comment (because they eat the EOL at the end)
    #   - block comments
    #   - semicolon
    #   - comma
    # We handle EOL implicitly in most cases by leaving PyParsing's default
    # whitespace definition as-is, which marks EOL as an ignored whitespace
    # character. However, sometimes Matlab syntax requires special care with
    # EOL, so in those cases, EOL is handled explicitly.

    _line_c_start  = Literal('%').suppress()
    _block_c_start = Literal('%{').suppress()
    _block_c_end   = Literal('%}').suppress()
    _line_comment  = Group(_line_c_start + restOfLine + _EOL)
    _block_comment = Group(_block_c_start + SkipTo(_block_c_end, include=True))
    _comment       = Group(_block_comment('comment') | _line_comment('comment'))

    _delimiter     = _COMMA | _SEMI
    _noncontent    = _delimiter | _comment | _EOL

    # Comma-separated arguments to matrix/array/cell arrays can have ':'
    # in arguments, but arguments to function calls can't.  Parameter lists in
    # some other situations (like function return values) can have '~', but
    # the other elements can only be identifiers, not expressions.  The
    # following are the different versions used in different places later on.
    #
    # For array parsing to work, the next bunch of grammar objects have to be
    # constructed with different whitespace-handling rules: they must not eat
    # line breaks, because we need to match EOL explicitly, or else we can't
    # properly parse a matrix like the following as consisting of 2 rows:
    #    a = [1 2
    #         3 4]
    # That's the reason for the next call to setDefaultWhitespaceChars().
    # This is turned off again further below.
    #
    # Also, the definitions of the array contents grammars below explicitly
    # include references to _WHITE, which normally would not be necessary and
    # considered redundant, *except* that in order to deal with some other
    # problems with array parsing, the definition of expressions used as
    # array contents explicitly turn off the regular whitespace rules.  This
    # is why whitespace appears in the next several terms.  So, if you find
    # yourself looking at these and thinking that the business involving
    # Optional(_WHITE) is useless and can be removed: no, they have to stay
    # in order to work properly inside other definitions later.
    #
    # Important note about _one_sub: handling MATLAB whitespace behavior
    # inside and outside of arrays is extremely challenging in this parsing
    # framework.  Here are examples of cases to be dealt with.  Suppose that
    # "a" is an array of one item:
    #
    #    a(1)        => one item, the value inside the array "a" at location 1
    #    a (1)       => one item, the value inside the array "a" at location 1
    #    [a (1)]     => an array of TWO items, the value of a and 1
    #    [(a (1))]   => an array of ONE item, a(1)
    #
    # Notice how in the 3rd example, the handling of whitespace changes inside
    # the array context, yet wrapping the same expression in parentheses once
    # again reverts the behavior of whitespace handling to how it is outside
    # the array context.  (Aside: WTF, MATLAB!?)  The solution implemented here
    # is rooted in the definition of _one_sub below, which references two
    # different expression grammar terms.  The first one, _expr_in_array,
    # handles the third example above.  The definition of _expr_in_array is a
    # variant of _expr that changes whitespace behavior such that whitespace
    # is not ignored.  This lets us handle the case where "a (1)" is
    # interpreted as two subscript items in the array context.  But, this
    # then screws up interpretation of the fourth example above, in which we
    # now want to revert handling of whitespace to what it is outside of an
    # array context.  That's the reason for the introduction of the separate
    # reference to _LPAR + _expr + _RPAR in the definition of _one_sub: it
    # lets us use the normal _expr to handle whitespace inside parenthesized
    # expressions as if they were outside the array context.

    ParserElement.setDefaultWhitespaceChars(' \t')

    _one_sub       = Group(_COLON('colon')) | _expr_in_array | _LPAR + _expr + _RPAR
    _comma_subs    = Optional(_one_sub) \
                     + ZeroOrMore(Optional(_WHITE) + _COMMA + Optional(_WHITE) + Optional(_one_sub))
    _space_subs    = _one_sub + ZeroOrMore(OneOrMore(_WHITE) + _one_sub)

    _call_args     = delimitedList(_expr)

    _opt_arglist   = Optional(_call_args('argument list'))

    _one_param     = Group(_TILDE) | Group(_id)
    _paramlist     = delimitedList(_one_param)
    _opt_paramlist = Optional(_paramlist('parameter list'))

    # Bare matrices.  This is a cheat because it doesn't check that all the
    # element contents have the same data type.  But again, since we expect our
    # input to be valid Matlab, we don't expect to have to verify that property.

    _row_sep       = Optional(_WHITE) + _SEMI + Optional(_WHITE) + Optional(_comment) \
                     | Optional(_WHITE) + _comment | _EOL
    _one_row       = _comma_subs('subscript list') ^ _space_subs('subscript list')
    _rows          = Optional(_WHITE) + Optional(Group(_one_row.leaveWhitespace())) \
                     + ZeroOrMore(_row_sep + Optional(Group(_one_row))) + Optional(_WHITE)
    _bare_array    = Group(_LBRACKET + _rows('row list') + _RBRACKET)('array')

    ParserElement.setDefaultWhitespaceChars(' \t\n\r')

    # Cell arrays.  You can write {} by itself, but a reference has to have at
    # least one subscript: "somearray{}" is not valid.  Newlines don't
    # seem to be allowed in args to references, but a bare ':' is allowed.
    # Some tricky parts:
    # - The following parses as a cell reference:        a{1}
    # - The following parses as a function call:         a {1}
    # - The following parses as an array of 3 elements:  [a {1} a]
    # - Cell array references can be nested: a{2}{3}

    _bare_cell     = Group(_LBRACE + Optional(_WHITE) + _rows('row list')
                           + Optional(_WHITE) + _RBRACE)('cell array')
    _cell_args     = Optional(_WHITE) + Group(_comma_subs)('subscript list') + Optional(_WHITE)
    _cell_base     = Group(_name + _LBRACE + _cell_args + _RBRACE)('cell array')
    _cell_nested   = Group(Group(_cell_base)('cell array')
                           + _LBRACE + _cell_args + _RBRACE)('cell array')
    _cell_access   = _cell_nested | _cell_base
    _cell_array    = _cell_access | _bare_cell

    # Named array references.  Note: this interacts with the definition of
    # function calls later below.  (See _funcall_or_array.)

    _array_args    = Group(_comma_subs)
    _array_base    = Group(_cell_access | _name)('array base')
    _array_access  = Group(_array_base
                           + _LPAR + _array_args('subscript list') + _RPAR
                          ).setResultsName('array')  # noqa

    # Function handles.
    #
    # See http://mathworks.com/help/matlab/ref/function_handle.html
    # In all function arguments, you can use a bare tilde to indicate a value
    # that can be ignored.  This is not obvious from the functional
    # documentation, but it seems to be the case when I try it.  (It's the
    # case for function defs and function return values too.)

    _named_handle  = Group('@' + _name)
    _anon_handle   = Group('@' + _LPAR + _opt_paramlist + _RPAR
                           + _expr('function definition'))  # noqa
    _fun_handle    = (_named_handle | _anon_handle).setResultsName('function handle')

    # Struct array references.  This is incomplete: in Matlab, the LHS can
    # actually be a full expression that yields a struct.  Here, to avoid an
    # infinitely recursive grammar, we only allow a specific set of objects
    # and exclude a full expr.  (Doing the obvious thing, expr + "." + _id,
    # results in an infinitely-recursive grammar.)  Also note _bare_array is
    # deliberately not part of the following because [1].foo is not legal.
    #
    # Dynamic field access means that 'str' in
    #    a.(str)
    # needs to be interpreted as something to be evaluated, not a static
    # identifier.  Thus, we can't return Identifier(name='str') alone, or
    # the caller will not be able to distinguish that from a static access,
    #    a.str
    # The solution here is to detect the use of ".()" and explicitly label
    # the type of field found (as either 'static field' or 'dynamic field').
    #
    # Note: BE VERY CAREFUL about the ordering of the terms in _struct_base.
    # A change to the order can lead to infinite recursion on some inputs.
    # The current order was determined by trial and error to work on our
    # various test cases.  (And no, I'm not proud of the hackiness.)

    _funcall_or_array   = Forward()
    _struct_field       = _id('static field') | _LPAR + _expr('dynamic field') + _RPAR
    _simple_struct_base = Group(_array_access | _id)
    _simple_struct      = Group(_simple_struct_base('struct base')
                                + Optional(_WHITE) + _DOT + Optional(_WHITE) 
                                + _struct_field)('struct')
    _struct_base        = Group(_simple_struct + Optional(_WHITE) + FollowedBy(_DOT)
                                ^ _fun_handle
                                ^ _funcall_or_array
                                ^ _cell_access
                                ^ _array_access
                                ^ _id)
    _struct_access      = Group(_struct_base('struct base')
                                + Optional(_WHITE) + _DOT + Optional(_WHITE)
                                + _struct_field)('struct')

    # "Function syntax" function calls.
    #
    # Unfortunately, the function call forms using parentheses look identical
    # to matrix/array accesses, and in fact in MATLAB there's no way to tell
    # them apart except by determining whether the first name is a function
    # or command.  This means it's ultimately run-time dependent, and depends
    # on the functions and scripts that the user has defined.
    #
    # We don't have access to the user's MATLAB environment, so we are left
    # to resort to various heuristics to try to guess what we have.  For
    # instance, if something comes through in "command syntax", we can assume
    # it's a function call.  (Handled by _funcall_cmd_style below.)  Another
    # one is that in arrays, you can use bare ':' in the argument list.  This
    # means that if a ':' is found, it's an array reference for sure.  (This
    # case is handled in the definition of _opt_arglist) Beyond that, we call
    # all cases we can't resolve syntactically as "array or function", and
    # then in post-processing, attempt to apply other heuristics to figure
    # out which ones are in fact functions.
    #
    # There are complications.  You can put function names or arrays inside a
    # cell array or struct, reference into that to get the function, and hand
    # it arguments.  E.g.:
    #    x = somearray{1}(x, 3)
    # or even
    #    somestruct(2).somefieldname = str2func('functionname')
    #    somestruct(2).somefieldname(42)
    #
    # The following definition is incomplete w.r.t. what MATLAB allows, since
    # MATLAB would probably let you use the full range of expressions as the
    # base for the function.

    _fun_access         = Group(_cell_access('cell array')) \
                          ^ Group(_simple_struct) \
                          ^ Group(_id)
    _funcall_or_array <<= Group(_fun_access('name')
                                + _LPAR + _opt_arglist + _RPAR
                               ).setResultsName('array or function')  # noqa

    # "Command syntax" function calls and array references.
    #
    # Matlab functions can be called with arguments either surrounded with
    # parentheses or not.  This is called "command vs. function syntax".
    # Here are examples of command syntax:
    #    clear x y z
    #    format long
    #    print -dpng magicsquare.png
    #    save /tmp/foo
    #    save relative/path.m
    # etc.  As the MATLAB docs say, the following are equivalent:
    #    load durer.mat        % Command syntax
    #    load('durer.mat')     % Function syntax
    # Note the way that the first form treats the arguments as (unquoted)
    # strings.  Also note that spaces are allowed in the second form but
    # do not turn the result into command-style syntax.  I.e.,
    #    load ('durer.mat')
    # is not the same as
    #    load '(\'durer.mat\')'
    #
    # The syntactic rules are explained in the following MATLAB document:
    # http://mathworks.com/help/matlab/matlab_prog/command-vs-function-syntax.html
    # The grammar below for command-style syntax is not fully compliant.  One
    # known failure: it requires an argument.  We deal with command-syntax
    # function calls *without* arguments separately in post-processing.

    ParserElement.setDefaultWhitespaceChars(' \t')

    _most_ops          = Group(_PLUS ^ _MINUS ^ _TIMES ^ _ELTIMES ^ _MRDIVIDE
                               ^ _MLDIVIDE ^ _RDIVIDE ^ _LDIVIDE ^ _MPOWER
                               ^ _ELPOWER ^ _LT ^ _LE ^ _GT ^ _GE ^ _EQ ^ _NE
                               ^ _AND ^ _OR ^ _SHORT_AND ^ _SHORT_OR ^ _COLON
                               ^ _NC_TRANSP)
    _noncmd_arg_start  = _EQUALS | _LPAR | _most_ops + _WHITE | _delimiter | _comment
    _dash_term         = Combine(Literal('-') + Word(alphas, alphanums + '_'))
    _fun_cmd_arg       = _STRING | _dash_term | CharsNotIn(" ,;\t\n\r")
    _fun_cmd_arglist   = _fun_cmd_arg + ZeroOrMore(NotAny(_noncontent)
                                                   + Optional(_WHITE)
                                                   + _fun_cmd_arg)
    _funcall_cmd_style = Group(_name + NotAny(_EOL)
                               + _WHITE + NotAny(_noncmd_arg_start)
                               + _fun_cmd_arglist('arguments')
                              )('command statement')

    ParserElement.setDefaultWhitespaceChars(' \t\n\r')

    # Function calls without parentheses.
    #
    # A final bit of nastiness in MATLAB is the ability to invoke a function
    # without using parenthese, such as this example:
    #
    #   if (rand > 0.50)
    #       A=1;
    #   end;
    #
    # Currently, we only recognize this case if the function involved is a
    # known MATLAB function or a function defined somewhere in the file.
    # This is done in post processing, but we tag the possible cases during
    # the initial parse by looking for _ambiguous_id instead of a plain _id.
    # This is why the following seemingly-pointless definition exists, and is
    # used instead of using _id directly in _operand and other similar places
    # later.

    _ambiguous_id = Group(NotAny(_reserved) + _identifier)('ambiguous id')

    # And now, general expressions and operators outside of arrays.

    _operand = Group(_funcall_or_array \
                     | _struct_access  \
                     | _array_access   \
                     | _cell_array     \
                     | _bare_array     \
                     | _fun_handle     \
                     | _ambiguous_id   \
                     | _NUMBER         \
                     | _STRING)

    _transp_op     = NotAny(_WHITE) + _NC_TRANSP ^ NotAny(_WHITE) + _CC_TRANSP
    _uplusminusneg = _UPLUS ^ _UMINUS ^ _UNOT
    _plusminus     = _PLUS ^ _MINUS
    _timesdiv      = _TIMES ^ _ELTIMES ^ _MRDIVIDE ^ _MLDIVIDE ^ _RDIVIDE ^ _LDIVIDE
    _power         = _MPOWER ^ _ELPOWER
    _logical_op    = _LE ^ _GE ^ _NE ^ _LT ^ _GT ^ _EQ
    _colon_op      = _COLON('colon operator')

    # In MATLAB, power and transpose have higher precedence than the unary
    # operators.  The next hack solves a problem in correctly matching
    # expressions in which a unary operator comes immediately after another
    # operator, particularly the _power operators.  The problem occurs
    # because of how infixNotation() constructs the matching expression
    # left-to-right as it goes down the list of arguments in the order given.
    # To get the right behavior, we have to set up _power to have higher
    # precendence than unary operators, which seems easy at first but it
    # turns out it interacts with the right-associative nature of unary
    # operators (_uplusminusneg).  For reasons that are not 100% clear, if
    # the first few terms are in the following (more intuitive, natural) order,
    #
    #   _expr <<= infixNotation(_operand, [
    #        (Group(_transp_op),     1, opAssoc.LEFT, makeLRlike(1)),
    #        (Group(_power),         2, opAssoc.LEFT, makeLRlike(2)),
    #        (Group(_uplusminusneg), 1, opAssoc.RIGHT),
    #       ...
    #
    # then an expression such as 2^-3 does not match.  The following hack
    # provides a second expression (_uplusminusneg_after) for matching the
    # unary operators if and only if they appear in the second operand of a
    # binary operator.
    #
    # The operator precedence rules in MATLAB are listed here:
    # http://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html

    _not_unary = _transp_op ^ _plusminus ^ _timesdiv ^ _power ^ _logical_op ^ _COLON
    _uplusminusneg_after = FollowedBy(_not_unary) + _UPLUS \
                           ^ FollowedBy(_not_unary) + _UMINUS \
                           ^ FollowedBy(_not_unary) + _UNOT

    _expr        <<= infixNotation(_operand, [
        (Group(_transp_op),                    1, opAssoc.LEFT, makeLRlike(1)),
        (Group(_uplusminusneg_after),          1, opAssoc.RIGHT),
        (Group(_power),                        2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_uplusminusneg),                1, opAssoc.RIGHT),
        (Group(_timesdiv),                     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_plusminus),                    2, opAssoc.LEFT, makeLRlike(2)),
        ((Group(_colon_op), Group(_colon_op)), 3, opAssoc.LEFT, makeLRlike(3)),
        (Group(_colon_op),                     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_logical_op),                   2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_AND),                          2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_OR),                           2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_AND),                    2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_OR),                     2, opAssoc.LEFT, makeLRlike(2)),
    ])

    # The 'end' keyword is special because of its many meanings.  One applies
    # when indexing arrays.  This next definition is so we can detect that.

    _end_op        = Keyword('end')('end operator')

    # MATLAB does something evil: the parsing behavior changes inside array
    # expressions.  This can be seen by typing the following expressions into
    # the MATLAB interpreter:
    #
    # 1 -1          result: 0
    # [1 -1]        result: array of 2 elements, [1, -1]
    # [1 - 1]       result: array of 1 element, [0]
    # [1 -1 - 1]    result: array of 2 elements, [1, -2]
    # 1 - 1         result: 0
    # 1-1           result: 0
    # [1- 1]        result: array of 1 element, [0]
    # [1 2 -3 + 4]  result: array of 3 elements, [1, 2, 1]
    # [1 2 -3 +4]   result: array of 4 elements, [1, 2, -3, 4]
    #
    # Another example was mentioned earlier in this file, involving the
    # definition of _one_sub.  Suppose that "a" is an array of one item:
    #
    #    a(1)        => one item, the value inside the array "a" at location 1
    #    a (1)       => one item, the value inside the array "a" at location 1
    #    [a (1)]     => an array of TWO items, the value of a and 1
    #    [(a (1))]   => an array of ONE item, a(1)
    #
    # The only solution I have found is to define the expression grammar
    # differently for the case of array contents.  This is the reason for
    # _expr_in_array, _funcall_or_array_in_array, and _operand_in_array
    # below; these versions change the interpretation of whitespace to make
    # it significant, to cause matching to prefer different interpretations
    # when used inside arrays.  Along with this, the definitions of arrays
    # and their subscripts earlier in this file also have explicit uses of
    # _WHITE in them, which wouldn't be necessary except for the fact that
    # _operand_in_array below uses leaveWhitespace() to cause whitespace to
    # be significant.
    #
    # Look, I know it's ugly.

    _plusminus_array = (OneOrMore(_WHITE) + (_PLUS ^ _MINUS).leaveWhitespace() + OneOrMore(_WHITE)) \
                       | (NotAny(_WHITE) + (_PLUS ^ _MINUS).leaveWhitespace())

    _funcall_or_array_in_array = Group(_fun_access('name')
                                       + _LPAR.copy().leaveWhitespace() + _opt_arglist + _RPAR
                                      ).setResultsName('array or function')  # noqa

    _operand_in_array = Group(_end_op
                              | _TILDE
                              | _funcall_or_array_in_array
                              | _struct_access
                              | _array_access
                              | _cell_array
                              | _bare_array
                              | _fun_handle
                              | _ambiguous_id
                              | _NUMBER
                              | _STRING
                             ).leaveWhitespace()

    _expr_in_array <<= infixNotation(_operand_in_array, [
        (Group(_transp_op),                    1, opAssoc.LEFT, makeLRlike(1)),
        (Group(_uplusminusneg_after),          1, opAssoc.RIGHT),
        (Group(_power),                        2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_uplusminusneg),                1, opAssoc.RIGHT),
        (Group(_timesdiv),                     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_plusminus_array),              2, opAssoc.LEFT, makeLRlike(2)),
        ((Group(_colon_op), Group(_colon_op)), 3, opAssoc.LEFT, makeLRlike(3)),
        (Group(_colon_op),                     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_logical_op),                   2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_AND),                          2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_OR),                           2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_AND),                    2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_OR),                     2, opAssoc.LEFT, makeLRlike(2)),
    ])

    # Assignments.
    #
    # We tag the LHS with 'lhs' whether it's a single variable or an array,
    # because we can distinguish the cases by examining the parsed object.

    _lhs_var        = Group(_id)
    _simple_assign  = Group(_lhs_var('lhs') + _EQUALS + _expr('rhs'))
    _lhs_array      = Group(_struct_access | _array_access | _cell_access | _bare_array)
    _other_assign   = Group(_lhs_array('lhs') + _EQUALS + _expr('rhs'))
    _assignment     = (_other_assign | _simple_assign).setResultsName('assignment')

    # Commands.
    #
    # Shell commands don't respect ellipses or delimiters, so we use EOL
    # explicitly here and match _shell_cmd at the _matlab_syntax level.

    _shell_cmd_cmd  = Group(restOfLine)('command')
    _shell_cmd      = Group(Group('!' + _shell_cmd_cmd + _EOL)('shell command'))

    # Control-flow statements.

    _control_stmt   = Forward()
    _stmt_list      = Forward()

    _single_expr    = _expr('expression') + Optional(FollowedBy(_noncontent))
    _test_expr      = _single_expr
    _body           = Group(_stmt_list)                    ('body')
    _break_stmt     = _BREAK                               ('break statement')
    _return_stmt    = _RETURN                              ('return statement')
    _continue_stmt  = _CONTINUE                            ('continue statement')

    _while_stmt     = Group(_WHILE + _test_expr
                            + _body
                            + _END)                        ('while statement')

    _loop_var       = Group(_id)                           ('loop variable')
    _for_version1   = _FOR + _loop_var + _EQUALS + _test_expr \
                      + _body \
                      + _END
    _for_version2   = _FOR + _LPAR + _loop_var + _EQUALS + _expr('expression') + _RPAR \
                      + _body \
                      + _END
    _for_stmt       = Group(_for_version2 | _for_version1) ('for statement')

    _catch_var      = Group(_id)                           ('catch variable')
    ParserElement.setDefaultWhitespaceChars(' \t')
    _catch_term     = _CATCH + Optional(NotAny(_noncontent) + _catch_var) + _noncontent
    ParserElement.setDefaultWhitespaceChars(' \t\n\r')
    _catch_body     = Group(_stmt_list)                    ('catch body')
    _try_stmt       = Group(_TRY
                            + _body
                            + Optional(_catch_term)
                            + _catch_body
                            + _END)                        ('try statement')

    _else_stmt      = Group(_ELSE + _body)                 ('else statement')
    _elseif_stmt    = Group(_ELSEIF + _test_expr + _body)
    _if_stmt        = Group(_IF + _test_expr
                            + _body
                            + ZeroOrMore(_elseif_stmt)     ('elseif statements')
                            + Optional(_else_stmt)
                            + _END).setResultsName         ('if statement')

    _case_stmt      = Group(_CASE + _test_expr + _body)
    _switch_other   = Group(_OTHERWISE + _body)            ('otherwise statement')
    _switch_stmt    = Group(_SWITCH + _test_expr
                            + ZeroOrMore(_case_stmt)       ('case statements')
                            + Optional(_switch_other)
                            + _END)                        ('switch statement')

    _control_stmt  <<= Group(_while_stmt
                             | _if_stmt
                             | _switch_stmt
                             | _for_stmt
                             | _try_stmt
                             | _continue_stmt
                             | _break_stmt
                             | _return_stmt
                            ).setResultsName('control statement')  # noqa

    # Global and persistent declarations.

    _scope_type     = Group(_PERSISTENT | _GLOBAL)         ('type')
    ParserElement.setDefaultWhitespaceChars(' \t')
    _scope_var_list = Group(_id) + ZeroOrMore(_WHITE + Group(_id)).leaveWhitespace()
    _scope_args     = _scope_var_list                      ('variables list')
    ParserElement.setDefaultWhitespaceChars(' \t\n\r')
    _scope_stmt     = Group(_scope_type + _scope_args)     ('scope declaration')

    # Standalone expressions.
    #
    # If an expression is written on a line outside of another construct,
    # it needs to be separated from other expressions by commas or newlines.

    ParserElement.setDefaultWhitespaceChars(' \t')
    _standalone_expr = _expr('standalone expression') + FollowedBy(_noncontent)
    ParserElement.setDefaultWhitespaceChars(' \t\n\r')

    # Statements and statement lists.
    #
    # Statement lists are almost the full _matlab_syntax, except that
    # they don't include function definitions.

    _stmt           = Group(_control_stmt
                            | _scope_stmt
                            | _assignment
                            | _funcall_cmd_style
                            | _standalone_expr)
    _stmt_list    <<= ZeroOrMore(_stmt ^ _shell_cmd ^ _noncontent)

    # Function definitions.
    #
    # When a function returns multiple values and the LHS is an array
    # expression in square brackets, a bare tilde can be put in place of an
    # argument value to indicate that the value is to be ignored.

    _fun_body       = Forward()

    _single_value   = Group(_id) | Group(_TILDE)
    _comma_values   = delimitedList(_single_value)
    _space_values   = OneOrMore(_single_value)
    _multi_values   = _LBRACKET + Optional(_comma_values ^ _space_values) + _RBRACKET
    _fun_outputs    = Group(_multi_values) | Group(_single_value)
    _fun_paramslist = _LPAR + _opt_paramlist + _RPAR

    # The 'end' in a function definition is optional in some cases and not in
    # others.  The use of 'end' is required for nested function definitions,
    # which means that we need two variants of function bodies too.  This
    # leads to our final grammatical indiginity: two expressions for function
    # definitions, which are used in the overall definition of _matlab_file
    # such that _matlab_file tries first one variant and then the other.
    # In the following two definitions, note that both the use of 'end' and
    # the definition of the body are different.

    _fun_without_end = Group(_FUNCTION
                             + Optional(_fun_outputs('output list') + _EQUALS())
                             + Optional(_WHITE) + _name
                             + Optional(_fun_paramslist)
                             + Group(_stmt_list)('body')
                            ).setResultsName('function definition')

    _fun_with_end   = Group(_FUNCTION
                            + Optional(_fun_outputs('output list') + _EQUALS())
                            + Optional(_WHITE) + _name
                            + Optional(_fun_paramslist)
                            + Group(_fun_body)('body')
                            + _END
                           ).setResultsName('function definition')

    # The next two definitions are only used to make the grouping level the
    # same as other statements in the overall grammar.

    _fun_def_shallow = Group(_fun_without_end)
    _fun_def_deep    = Group(_fun_with_end)

    # And now, the function body for function definitions that permit nesting.
    # (Bodies that don't allow function nesting simply use _stmt_list.)

    _fun_body <<= ZeroOrMore(_fun_def_deep ^ _stmt ^ _shell_cmd ^ _noncontent)

    # The complete MATLAB file syntax.
    #
    # In MATLAB, a file cannot mix the style of function definitions that use
    # ends: either they all have to have 'end', or none do.  This leads to two
    # forms of MATLAB files.  The following would be the correct definition:
    #
    #  _matlab_file = (ZeroOrMore(_fun_def_shallow ^ _stmt ^ _shell_cmd ^ _noncontent)
    #                  ^ ZeroOrMore(_fun_def_deep ^ _stmt ^ _shell_cmd ^ _noncontent))
    #
    # However, using that grammar definition, the resulting MOCCASIN parser
    # takes almost twice as long to parse anything as it would if only one of
    # those versions was present.  Since MOCCASIN already assumes that input
    # files are valid MATLAB, we relax the definition to the following form
    # to gain a substantial speedup.  This is not strictly correct because it
    # allows mixing the forms.  (MOCCASIN passes all our syntactic tests
    # either way, but probably would fail to reject some invalid inputs.)

    _matlab_file = ZeroOrMore(_fun_def_shallow ^ _fun_def_deep ^ _stmt ^ _shell_cmd ^ _noncontent)


    # Preprocessor.
    # .........................................................................
    # This is used to process the input before it is handed to the actual
    # parser defined by the grammar above.  We do this to overcome
    # limitations in our PyParsing-based grammar.
    #
    # Notes about continuation processing.  Continuations in MATLAB can
    # appear anywhere, including in the middle of expressions.  However,
    # continuations in MATLAB are not recognized inside (1) strings and (2)
    # shell command lines, where the ellipsis sequence "..." is left intact.
    # In a sense, continuations are almost like PyParsing's notion of ignored
    # expressions, except that they need to be interpreted as spaces.  It
    # could have been handled using PyParsing ignore() facility, if that
    # facility supported parse actions, but it turns out that something set
    # as ignored in PyParsing is truly ignored -- the associated parse
    # actions are also ignored, so we have no way of doing the replacement.
    # I previously did implement continuations as ignored expressions, and
    # then discovered this is wrong in cases such as this:
    #     [a...
    #     b]
    # This is wrong because if you simply ignore the ellipsis, this turns into
    #     [a
    #     b]
    # which gets parsed as a column vector, whereas what MATLAB actually does
    # in this case is parse it as a row vector:
    #     [a b]
    # MATLAB does this because the ellipsis sequence is turned into a space;
    # which is not the same as ignoring it completely.
    #
    # Currently, MOCCASIN does not handle continuations well: it always
    # replaces them, even inside strings and shell commands, because in our
    # application we don't do anything with strings and shell commands
    # anyway.  We can afford to munge them.  We use this cheap approach
    # because it's difficult to avoid matching inside strings and shell
    # commands.  A better approach would be something like the following: (1)
    # preprocess the input to store all strings and shell commands and
    # replace them in the input with temporary markers, (2) do the
    # continuation replacements, (3) go back and replace the markers with the
    # stored strings and shell commands.

    _continuation  = Combine(_ELLIPSIS.leaveWhitespace()
                             + Optional(CharsNotIn('\n\r\f')('comment'))
                             + _EOL + _SOL)

    _continuation.setParseAction(lambda t: ' ')

    def _preprocess(self, input):
        # Remove DOS-style carriage returns from the input.
        input = input.replace('\r\n', '\n')
        # Remove continuations.
        return self._continuation.transformString(input)


    # Generator for final MatlabNode-based output representation.
    #
    # The following post-processes the ParseResults-based output from PyParsing
    # and creates our format consisting of MatlabContext and MatlabNode.
    # .........................................................................

    def _generate_nodes_and_contexts(self, pr):
        # Start by creating a context for the overall input.
        self._push_context(MatlabContext(topmost=True))

        # 1st pass: visit ParseResults items, translate them to MatlabNodes,
        # and create contexts for function definitions encountered.
        nodes = [ParseResultsTransformer(self).visit(item) for item in pr]

        # 2nd & 3rd passes: infer the types of objects where possible, and
        # transform some classes into others to overcome limitations in our
        # initial parse.  Must be done twice to propagate inferences.
        nodes = NodeTransformer(self).visit(nodes)
        nodes = NodeTransformer(self).visit(nodes)

        # Final step: if the first construct in this file (after possible
        # comments) is a function definition, this whole file is a function.
        # Indicate this by assigning the name to the top level context.
        (is_function_file, function_name) = self._find_first_function(nodes)
        if is_function_file:
            self._context.name = function_name

        self._context.nodes = nodes
        return self._context


    # Context and scope management.
    #
    # This block is used by the code that converts the PyParsing output to
    # our MatlabNode and MatlabContext objects.
    #
    # In Matlab, an input file will be either a script, or a function
    # definition.  A script is distinguished from a function definition
    # simply by not starting with "function ..." (after any initial comments
    # in the file).
    #
    # Files can contain nested function definitions.  Each of these sets up
    # contexts, inside of which can be more matlab commands such as variable
    # assignments.  For our purposes, we're particularly interested in
    # tracking functions, so the context-tracking scheme in grammar.py is
    # organized around function definitions.
    #
    # To track nested function definitions, grammar.py has a notion of
    # "contexts".  A context is a MatlabContext object.  It holds the
    # functions, variables and other definitions found at a particular level
    # of nesting.
    #
    # The outermost context is the file.  Each time a new function
    # declaration is encountered, another context is "pushed".  The context
    # pushed is a MatlabContext object containing the parsing results
    # returned for a function definition.  When an 'end' statement is
    # encountered in the input, the current context is popped.
    # .........................................................................

    def _push_context(self, newcontext):
        newcontext.parent = self._context
        self._context = newcontext


    def _pop_context(self):
        # Don't pop topmost context.
        if self._context.parent and not self._context.topmost:
            self._context = self._context.parent


    def _save_function_definition(self, node):
        newcontext = MatlabContext(name=node.name, parent=self._context,
                                   parameters=node.parameters,
                                   returns=node.output, pr=None, topmost=False)
        self._context.functions[node.name] = newcontext
        return newcontext


    def _save_function_call(self, node):
        # Save each call as a list of the arguments to the call.
        # This will thus be a list of lists.
        if node.name not in self._context.calls:
            self._context.calls[node.name] = [node.args]
        else:
            self._context.calls[node.name].append(node.args)


    def _save_assignment(self, node):
        self._context.assignments[node.lhs] = node.rhs


    def _get_assignment(self, node, context, recursive=False):
        if node in self._context.assignments:
            value = self._context.assignments[node]
            if isinstance(value, Identifier) and recursive:
                ultimate_value = self._get_assignment(value, context, True)
                return ultimate_value or value
            else:
                return value
        elif hasattr(context, 'parent') and context.parent:
            return self._get_assignment(self, node, context.parent)
        else:
            return None


    def _save_type(self, thing, type):
        self._context.types[thing] = type


    def _get_type(self, thing, context):
        if thing in context.types:
            return context.types[thing]
        elif hasattr(context, 'parent') and context.parent:
            return self._get_type(thing, context.parent)
        elif isinstance(thing, Ambiguous) or isinstance(thing, FunCall):
            if isinstance(thing.name, Identifier):
                name = thing.name.name
                return 'function' if matlab_function_or_command(name) else None
            else:
                return None
        elif isinstance(thing, Identifier):
            return 'function' if matlab_function_or_command(thing.name) else None
        return None


    def _get_direct_calls(self, name, context, anywhere=False, recursive=False):
        calls = []
        if context.calls and name in context.calls:
            calls += context.calls[name]
        if anywhere and context.functions:
            for fun_name, fun_context in context.functions.items():
                if name == fun_name:
                    continue
                calls += self._get_direct_calls(name, fun_context, False, False)
        if recursive and hasattr(context, 'parent') and context.parent:
            calls += self._get_direct_calls(name, context.parent, anywhere, True)
        return [x for x in calls if x]


    def _get_indirect_calls(self, name, context, anywhere=False, recursive=False):
        # Search function calls, looking for cases where the named function is
        # passed in as a function handle.
        calls = defaultdict(list)
        for fun_name in (context.calls or []):
            for arglist in context.calls[fun_name]:
                for arg in (arglist or []):
                    if isinstance(arg, FuncHandle) and name == arg.name:
                        calls[fun_name].append(arglist)
        if anywhere and context.functions:
            for fun_name, fun_context in context.functions.items():
                calls.update(self._get_indirect_calls(name, fun_context, False, False))
        if recursive and hasattr(context, 'parent') and context.parent:
            calls.update(self._get_indirect_calls(name, context.parent, anywhere, True))
        return calls


    def _find_first_function(self, nodes):
        for node in nodes:
            if isinstance(node, Comment):
                continue
            if isinstance(node, FunDef):
                return (True, node.name)
            else:
                return (False, None)
        return (False, None)


    # The core parser invocation.
    # .........................................................................

    def _do_parse(self, input):
        preprocessed = self._preprocess(input)
        pr = self._matlab_file.parseString(preprocessed, parseAll=True)
        return self._generate_nodes_and_contexts(pr)


    # Debugging.
    # .........................................................................

    # Name each grammar object after itself, so that when PyParsing prints
    # debugging output, it uses the name rather than a generic regexp term.

    _to_name = [ _AND, _CC_TRANSP, _COLON, _COMMA, _DOT, _ELLIPSIS, _ELPOWER,
                 _ELTIMES, _END, _EOL, _EQ, _EQUALS, _EXPONENT, _FLOAT,
                 _FUNCTION, _GE, _GT, _INTEGER, _LBRACE, _LBRACKET, _LDIVIDE,
                 _LE, _LPAR, _LT, _MINUS, _MLDIVIDE, _MPOWER, _MRDIVIDE,
                 _NC_TRANSP, _NE, _NUMBER, _OR, _PLUS, _RBRACE, _RBRACKET,
                 _RDIVIDE, _RPAR, _SEMI, _SHORT_AND, _SHORT_OR, _SOL,
                 _STRING, _TILDE, _TIMES, _UMINUS, _UNOT, _UPLUS, _WHITE,
                 _ambiguous_id, _anon_handle, _array_access, _array_args,
                 _array_base, _assignment, _bare_array, _bare_cell,
                 _block_c_end, _block_c_start, _block_comment, _body,
                 _break_stmt, _call_args, _case_stmt, _catch_body,
                 _catch_term, _catch_var, _cell_access, _cell_args,
                 _cell_array, _cell_base, _cell_nested, _colon_op,
                 _comma_subs, _comma_values, _comment, _continue_stmt,
                 _control_stmt, _control_stmt, _dash_term, _delimiter,
                 _else_stmt, _elseif_stmt, _end_op, _expr, _expr_in_array,
                 _expr_in_array, _for_stmt, _for_version1, _for_version2,
                 _fun_access, _fun_body, _fun_cmd_arg, _fun_cmd_arglist,
                 _fun_def_deep, _fun_def_shallow, _fun_handle, _fun_outputs,
                 _fun_paramslist, _fun_with_end, _fun_without_end,
                 _funcall_cmd_style, _funcall_or_array, _id , _identifier,
                 _if_stmt, _lhs_array, _lhs_var, _line_c_start,
                 _line_comment, _logical_op, _loop_var, _matlab_file,
                 _most_ops, _multi_values, _name, _named_handle,
                 _noncmd_arg_start, _noncontent, _not_unary, _one_param,
                 _one_row, _one_sub, _operand, _operand_in_array,
                 _opt_arglist, _opt_paramlist, _other_assign, _paramlist,
                 _plusminus, _plusminus_array, _power, _reserved,
                 _return_stmt, _row_sep, _rows, _scope_args, _scope_stmt,
                 _scope_type, _scope_var_list, _shell_cmd, _shell_cmd_cmd,
                 _simple_assign, _simple_struct, _simple_struct_base,
                 _single_expr, _single_value, _space_subs, _space_values,
                 _standalone_expr, _stmt, _stmt_list, _stmt_list,
                 _struct_access, _struct_base, _struct_field, _switch_other,
                 _switch_stmt, _test_expr, _timesdiv, _transp_op, _try_stmt,
                 _uplusminusneg, _uplusminusneg_after, _while_stmt]

    def _object_name(self, obj):
        """Returns the name of a given object."""
        try:
            values = MatlabGrammar.__dict__.iteritems()  # Python 2
        except:
            values = MatlabGrammar.__dict__.items()      # Python 3
        for name, thing in values:
            if thing is obj:
                return name


    _init_grammar_names_done = []

    def _init_grammar_names(self):
        if 'done' not in self._init_grammar_names_done:
            for obj in self._to_name:
                obj.setName(self._object_name(obj))
            self._init_grammar_names_done.append('done')


    # The next variable and function are for printing low-level PyParsing
    # matches.  You can reduce the amount of output by changing the value
    # (which is _to_name by default) to a list of specific objects.  E.g.:
    #    _to_print_debug = [_cell_access, _cell_array, _bare_cell, _expr]

    _to_print_debug = _to_name # [_fun_body, _fun_def_deep, _fun_def_shallow, _stmt, _matlab_file]

    def _print_debug(self, print_debug=False):
        if print_debug:
            for obj in self._to_print_debug:
                obj.setDebug(True)


    # Instance initialization.
    # .........................................................................

    def __init__(self):
        self._init_grammar_names()
        # self._init_parse_actions()
        self._print_debug(False)
        self._reset()


    def __enter__(self):
        self._reset()
        return self


    def __exit__(self, exception_type, exception_value, tb):
        if exception_type:
            traceback.print_tb(tb)
            raise MatlabInternalException(exception_value)
        return self


    def _reset(self):
        self._context = None
        self._push_context(MatlabContext(topmost=True))


    # External interfaces.
    # .........................................................................

    def parse_string(self, input, print_results=False, print_debug=False,
                     fail_soft=False):
        """Parses MATLAB input and returns an a MatlabContext object.

        :param print_debug: print complete parsing debug output.
        :param print_results: print the internal presentation of the results.
        :param fail_soft: don't raise an exception if parsing fails.

        Warning: print_debug produces *a lot* of output.  Don't use it on
        anything more than a few lines of input.
        """
        self._reset()
        try:
            self._print_debug(print_debug)
            top_context = self._do_parse(input)
            if print_results:
                self.print_parse_results(top_context)
            return top_context
        except ParseException as err:
            msg = "Error: {0}".format(err)
            if fail_soft:
                print(msg)
                return None
            else:
                msg = 'Failed to parse MATLAB input'
                raise MatlabParsingException(msg)


    def parse_file(self, path, print_results=False, print_debug=False,
                   fail_soft=False):
        """Parses the MATLAB contained in `file` and returns a MatlabContext.
        object This is essentially identical to MatlabGrammar.parse_string()
        but does the work of opening and closing the `file`.

        :param print_debug: print complete parsing debug output.
        :param print_results: print the internal presentation of the results.
        :param fail_soft: don't raise an exception if parsing fails.

        Warning: print_debug produces *a lot* of output.  Don't use it on
        anything more than a few lines of input.
        """
        self._reset()
        try:
            file = codecs.open(path)
            contents = file.read()
            self._print_debug(print_debug)
            top_context = self._do_parse(contents)
            top_context.file = path
            file.close()
            if print_results:
                self.print_parse_results(top_context)
            return top_context
        except Exception as err:
            msg = "Error: {0}".format(err)
            if fail_soft:
                print(msg)
                return None
            else:
                msg = 'Failed to parse MATLAB input'
                raise MatlabParsingException(msg)


    def print_parse_results(self, results, print_raw=False):
        """Prints a representation of the parsed output given in `results`.
        This is intended for debugging purposes.  If `print_raw` is True,
        prints the underlying Python objects of the representation.  The
        objects in the output are valid Python objects, and in theory could
        be used to recreate the input or or less exactly.

        If `print_raw` is False (the default), prints the output in a
        slightly more human-readable form.
        """
        if not isinstance(results, MatlabContext):
            raise ValueError("Expected a MatlabContext object")
        if print_raw:
            print('[')
            for node in results.nodes:
                print(repr(node))
            print(']')
        else:
            for node in results.nodes:
                print(node)


    @staticmethod
    def make_formula(thing, spaces=True, parens=True, atrans=None):
        """Converts a mathematical expression into libSBML-style string form.
        The default behavior is to put spaces between terms and operators; if
        the optional flag 'spaces' is False, then no spaces are introduced.
        The default is also to surround the expression with parentheses but
        if the optional flag 'parens' is False, the outermost parentheses
        (but not other parentheses) are omitted.  Finally, if given a
        function for parameter 'atrans' (default: none), it will call that
        function when it encounters array references.  The 'atrans' function
        will be given one argument, the array object; it should return a text
        string corresponding to the value to be used in place of the array.
        If no 'atrans' is given, the default behavior is to render arrays
        as they would appear in Matlab text: e.g., "foo(2,3)".
        """
        def compose(name, args, delimiters=None):
            list = [MatlabGrammar.make_formula(arg, spaces, parens, atrans)
                    for arg in (args or [])]
            sep = ' ' if spaces else ''
            front = name if name else ''
            left = delimiters[0] if delimiters else ''
            right = delimiters[1] if delimiters else ''
            return front + left + sep.join(list) + right

        recurse = MatlabGrammar.make_formula
        if isinstance(thing, str):
            return thing
        elif isinstance(thing, Primitive):
            return MatlabNode.as_string(thing.value)
        elif isinstance(thing, Identifier):
            return MatlabNode.as_string(thing.name)
        elif isinstance(thing, ArrayRef) or isinstance(thing, Ambiguous):
            if atrans:
                return atrans(thing)
            if isinstance(thing.name, Identifier):
                aname = thing.name.name
            else:
                aname = recurse(thing.name, spaces, parens, atrans)
            return compose(aname, thing.args, '()')
        elif isinstance(thing, FunCall):
            return compose(thing.name.name, thing.args, '()')
        elif (isinstance(thing, StructRef) or isinstance(thing, FuncHandle)
              or isinstance(thing, AnonFun)):
            # FIXME: we don't have a sensible equivalent in SBML.
            return MatlabNode.as_string(thing)
        elif isinstance(thing, Operator):
            if isinstance(thing, UnaryOp):
                operand = recurse(thing.operand, spaces, parens, atrans)
                return compose(None, [thing.op, operand], '()')
            elif isinstance(thing, BinaryOp):
                left = recurse(thing.left, spaces, parens, atrans)
                right = recurse(thing.right, spaces, parens, atrans)
                return compose(None, [left, thing.op, right], '()')
            elif isinstance(thing, ColonOp):
                # FIXME: we don't have a sensible equivalent in SBML.
                left = recurse(thing.left, spaces, parens, atrans)
                right = recurse(thing.right, spaces, parens, atrans)
                if thing.middle:
                    middle = recurse(thing.middle, spaces, parens, atrans)
                    return left + ':' + middle + ':' + right
                else:
                    return left + ':' + right
            elif isinstance(thing, Transpose):
                # FIXME: we don't have a sensible equivalent in SBML.
                return recurse(thing.operand, spaces, parens, atrans) + thing.op

        elif isinstance(thing, Array):
            # FIXME: we don't have arrays in core SBML.
            return compose(None, thing.rows, '[]')

        elif isinstance(thing, list):
            return compose(None, thing, '()')
        elif 'comment' in thing:
            return ''
        else:
            # The remaining cases are things like command statements.  Those
            # shouldn't end up being called for make_formula.  Rather than
            # raise an error, though, this just returns None and lets the
            # caller deal with the problem.
            return None


# Notes about dealing with the intermediate PyParsing-based representation.
# .............................................................................
#
# First thing to know: the ParseResults objects generated by this
# PyParsing-based parser are heavily nested and annotated.  This is annoying
# to traverse by hand, and even more annoying to print (you will a *lot* of
# output for even simple things).  More on that below.
#
# The second thing to note is that the grammar is designed to attach
# PyParsing "result names" to matched components.  What this means is that
# most ParseResults objects have a Python dictionary associated with them.
# You can use Python's keys() operator to inspect the dictionary keys on most
# objects.  The basic approach to using the parsing results thus becomes a
# matter of using keys() to find out the entry or entries on an object,
# accessing the dictionary entries using the keys, calling keys() on the
# result of *that*, and so on, recursively.
#
# Here's an example using a simple assignment.  Suppose a file contains this:
#
#     a = 1
#
# This will return one ParseResults object at the top level, but this object
# will in reality be a recursively-structured list of annotated ParseResults
# objects.  (This will hopefully become more clear as this example
# progresses.)  At the top level, there will be one object per line in the
# file.  To find out how many there are, you can look at the length of what
# was returned by pyparsing's parseString(...):
#
#     (Pdb) type(results)
#     <class 'pyparsing.ParseResults'>
#     (Pdb) len(results)
#     1
#
# In this example, there's only one line in the file, so the length of the
# ParseResults object is one.  Let's get the ParseResults object for that
# first line:
#
#     (Pdb) content = results[0]
#     (Pdb) content.keys()
#     ['assignment']
#
# This first line of the file was labeled as an 'assignment', which is
# MatlabGrammar's way of identifying (you guessed it) an assignment
# statement.  Now let's look inside of it:
#
#     (Pdb) content['assignment'].keys()
#     ['rhs', 'lhs']
#
# The object stored under the dictionary key 'assignment' has its own
# dictionary, and that dictionary has two entries: one under the key 'lhs'
# (for the left-hand side of the assignment) and another under the key 'rhs'
# (for the right-hand side).  You can access each of these individually:
#
#     (Pdb) content['assignment']['lhs'].keys()
#     ['identifier']
#
# This now says that the object keyed by 'lhs' in the content['assignment']
# ParseResults object has another dictionary, with a single item stored under
# the key 'identifier'.  'identifier' is one of the terminal entities in
# MatlabGrammar.  When you access its value, you will find it's not a
# ParseResults object, but a string:
#
#     (Pdb) content['assignment']['lhs']['identifier']
#     'a'
#
# And there it is: the name of the variable on the left-hand side of the
# assignment in the file.  If we repeat the process for the right-hand side
# of the assignment, we find the following:
#
#     (Pdb) content['assignment']['rhs'].keys()
#     ['number']
#     (Pdb) content['assignment']['rhs']['number']
#     '1'
#
# The key 'number' corresponds to another terminal entity in MatlabGrammar.
# Its value is (you guessed it again) a number.  Note that the values
# returned by MatlabGrammar are always strings, so even though it could in
# principle be returned in the form of a numerical data type, MatlabGrammar
# does not do that, because doing so might require data type conversions and
# such conversions might require decisions that are best left to the
# applications calling MatlabGrammar.  So instead, it always returns
# everything in finds in a MATLAB file as a text string.
#
# Now, let's examine what happens if we have something slightly more
# complicated in the file, such as the following:
#
#     a = [1 2; 3 4]
#
# This is an assignment to an array that has two rows, each of which have two
# items.  Applying the parser to this input will once again yield a
# ParseResults object that itself contains a list of ParseResults objects,
# where the list will only have length one.  If we access the object,
#
#     (Pdb) content = results[0]
#     (Pdb) content.keys()
#     ['assignment']
#
# we once again have an assignment, as expected.  Let's take a look at the
# right-hand side of this one:
#
#     (Pdb) content['assignment']['rhs'].keys()
#     ['array']
#
# This time, MatlabGrammar has helpfully identified the object on the
# right-hand side as an array.  In the MATLAB world, a "matrix" is a
# two-dimensional array, but the MatlabGrammar grammar is not able to
# determine the number of dimensions of an array object; consequently, all of
# the homogeneous array objects (vectors, matrices, and arrays) are labeled
# as simply 'array'.  (MATLAB cell arrays are labeled 'cell array'.)  Now
# let's traverse the structure it produced:
#
#     (Pdb) array = content['assignment']['rhs']['array']
#     (Pdb) array.keys()
#     ['row list']
#     (Pdb) array['row list'].keys()
#     []
#
# This time, the object has no keys.  The reason for this is the following:
# some objects stored under the dictionary keys are actually lists.  The name
# 'row list' is meant to suggest this possibility.  When a value created by
# MatlabGrammar is a list, the first thing to do is to find out its length:
#
#     (Pdb) len(array['row list'])
#     2
#
# What this means is that the array has two row entries stored in a list
# keyed by 'row list'.  Accessing them is simple:
#
#     (Pdb) row1 = array['row list'][0]
#     (Pdb) row2 = array['row list'][1]
#     (Pdb) row1.keys()
#     ['subscript list']
#     (Pdb) row2.keys()
#     ['subscript list']
#
# Both of them have lists of their own.  These work in the same way as the
# row lists: you first find out their length, and then index into them to get
# the values.
#
#     (Pdb) len(row1)
#     2
#     (Pdb) row1[0].keys()
#     ['number']
#     (Pdb) row1[0]['number']
#     '1'
#
# As expected, we are down to the terminal parts of the expression, and here
# we have indexed into the first element of the first row of the array.  All
# of the rest of the entries in the array are accessed in the same way.  For
# example,
#
#     (Pdb) row2[1].keys()
#     ['number']
#     (Pdb) row2[1]['number']
#     '4'
#
# As a final example, let's take a look at a mathematical expression.
# Suppose our file contains the following:
#
#     a = 1 + 2
#
# As usual, applying the parser to this input will once again yield a
# ParseResults object that itself contains a list of ParseResults objects,
# and once again the list will only have length 1 because there is only one
# line in the file.  If we access the first object,
#
#     (Pdb) content = results[0]
#     (Pdb) content.keys()
#     ['assignment']
#
# we once again have an assignment, as expected.  Let's take a look at the
# right-hand side of this one:
#
#     (Pdb) content['assignment']['rhs'].keys()
#     []
#
# This time, the right-hand side does not have a key.  This is the tip-off
# that the right-hand side is an expression: in MatlabGrammar, if there is no
# key on an object, it means that the object is an expression or a list.
# Expressions are lists: when you encounter them, it means the next step is
# to iterate over the elements.
#
#     (Pdb) len(content['assignment']['rhs'])
#     3
#     (Pdb) content['assignment']['rhs'][0].keys()
#     ['number']
#     (Pdb) content['assignment']['rhs'][1].keys()
#     ['binary operator']
#     (Pdb) content['assignment']['rhs'][2].keys()
#     ['number']
#
# In this simple expression, the elements inside the expression list are
# terminal objects, but in general, they could be anything, including more
# expressions.  The rule for traversing expressions is the same: inspect the
# keys of each object, do whatever is appropriate for kind of object it is,
# and if there are no keys, it's another expression, so traverse it
# recursively.
#
# And that summarizes the basic process for working with MatlabGrammar parse
# results.  The parser(...) returns a list of objects results for the lines
# in the file; each has a dictionary, which you inspect to figure out what
# kind of objects were extracted, and then you dig into the object's
# dictionaries recursively until you reach terminal entities.  Sometimes the
# values for dictionaries are lists, in which case you iterate over the
# values, applying the same principle.
