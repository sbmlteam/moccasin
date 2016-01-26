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
# forms using parentheses look identical to matrix/array accesses, and in
# fact, in MATLAB there's no way to tell them apart on the basis of syntax
# alone.  A program must determine whether the first name is a function or
# command, which means it's ultimately run-time dependent and depends on the
# functions and scripts that the user has defined.  However, as mentioned
# above, one of the core goals of MOCCASIN is to be able to run independently
# of the user's environment (and indeed, without using MATLAB at all): in
# other words, _MOCCASIN does not have access to the user's MATLAB
# environment_, so it must resort to various heuristics to try to guess
# whether a given entity is meant to be an array reference or a function
# call.  It often cannot, and then it can only return `ArrayOrFunCall` as a
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
# |  |  |  +- FunHandle     # A function handle, e.g., "@foo"
# |  |  |  `- AnonFun       # An anonymous function, e.g., "@(x,y)x+y".
# |  |  |
# |  |  `- Reference        # Objects that point to values.
# |  |     +- Identifier
# |  |     +- ArrayOrFunCall
# |  |     +- FunCall
# |  |     +- ArrayRef
# |  |     `- StructRef
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
# |  +- TryCatch
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
#      objects may be regular arrays or cell arrays.  In this parser and the
#      Python representation, both types of arrays are treated mostly
#      identically, with only a Boolean attribute (`is_cell`) in `Array` to
#      distinguish them.
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
#      `ArrayOrFunCall` objects represent something that cannot be
#      distinguished as either an array reference or a named function call.
#      This problem is discussed in a separate section below.  If the parser
#      *can* infer that a given term is an array reference or a function
#      call, then it will report them as `ArrayRef` or `FunCall`,
#      respectively, but often it is impossible to tell and the parser must
#      resort to using `ArrayOrFunCall`.
#
# * `Operator` objects are tree-structured combinations of operators and
#   `Entity` objects.  Operators generally have an attribute that represents
#   the specific operation (e.g., `+` or `./`), and operands; depending on
#   the operator, there may be one or more operands.
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
# parsing this, and the context object will have one attribute, `nodes`,
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
# parsing results.  (It is worth keeping in mind at this point that _MOCCASIN
# does not have access to the user's MATLAB environment_.)
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
# 3. MOCCASIN has a list of known MATLAB functions and commands.  (The list
#    is stored in the file `functions.py` and was generated by inspecting the
#    MATLAB documentation for the 2014b version of MATLAB.)  If an ambiguous
#    array reference or function call has a name that appears on this list,
#    it is inferred to be a `FunCall` and not an `ArrayRef`.
#
# 4. In all other cases, it will label the object `ArrayOrFunCall`.
#
# Users will need to do their own processing when they encounter a
# `ArrayOrFunCall` object to determine what kind of thing the object really
# is.  In the most general case, MOCCASIN can't tell from syntax alone
# whether something could be a function, because without running MATLAB (and
# doing it _in the user's environment_, since the user's environment affects
# the functions and scripts that MATLAB knows about), it simply cannot know.
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
# attribute on `StructRef` called `dynamic_access`.  Its value is `True` if
# the `StructRef` attribute `field` is something that is meant to be
# evaluated.
#

# Preface material.
# .............................................................................

from __future__ import print_function
import pdb
import sys
import copy
import pyparsing                        # Need this for version check, so ...
from pyparsing import *                 # ... DON'T merge this & previous stmt!
from distutils.version import LooseVersion
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

#        pdb.set_trace()
        if len(pr) > 1 and empty_dict(pr):
            # It's an expression.  We deconstruct the infix notation.
            if len(pr) == 2 and 'unary operator' in pr[0].keys():
                return self.visit_unary_operator(pr)
            elif len(pr) == 3:
                if 'binary operator' in pr[1].keys():
                    return self.visit_binary_operator(pr)
                elif 'colon operator' in pr[1].keys():
                    return self.visit_colon_operator(pr)

        # Not an expression, but an individual, single parse result.
        # We dispatch to the appropriate transformer by building the name.
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
        # 'end' should be the only keyword we ever encounter.
        # FIXME this needs to be checked more closely.
        if 'end' in pr['end operator']:
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
        # This is needed because PyParsing's infixNotation(), used in our
        # Matlab grammar definition, does not support ternary operators.  So,
        # we currently define ':' as being binary when it appears in an
        # expression context, which in turn leads to a ternary ':' expression
        # becoming a nested list of two binary operators.  FIXME: ask the
        # PyParsing developer for a way to do ternary operators properly.
        if empty_dict(pr[0]) and len(pr[0]) == 3 \
           and 'colon operator' in pr[0][1].keys():
            left=self.visit(pr[0][0])
            middle=self.visit(pr[0][2])
            right=self.visit(pr[2])
        else:
            left=self.visit(pr[0])
            middle=None
            right=self.visit(pr[2])
        return ColonOp(left=left, middle=middle, right=right)


    def visit_transpose(self, pr):
        content = pr['transpose']
        the_op = content['operator']
        the_operand = self.visit(content['operand'])
        return Transpose(op=the_op, operand=the_operand)


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
        # ambiguous function call or array access).  If we have a name, it's
        # the latter; if we have a row list, it's the former.
        if 'name' in content:
            # Array reference.
            the_name = self.visit(content['name'])
            the_subscripts = self._convert_list(content['subscript list'])
            return ArrayRef(name=the_name, args=the_subscripts, is_cell=False)
        elif 'row list' in content:
            # Bare array.
            return Array(rows=self._convert_rows(content['row list']), is_cell=False)
        else:
            # No row list or subscript list => empty array.
            return Array(rows=[], is_cell=False)


    def visit_cell_array(self, pr):
        content = pr['cell array']
        # This is basically like regular arrays.  Again, two kinds of
        # situations: a bare cell array, and one where we managed to
        # determine it's an array access.  If we have a name, it's the
        # latter; if we have a row list, it's the former.
        if 'name' in content:
            # Array reference.
            the_name = self.visit(content['name'])
            the_subscripts = self._convert_list(content['subscript list'])
            return ArrayRef(name=the_name, args=the_subscripts, is_cell=True)
        elif 'row list' in content:
            # Bare array.
            return Array(rows=self._convert_rows(content['row list']), is_cell=True)
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
        return ArrayOrFunCall(name=the_name, args=the_args)


    def visit_function_handle(self, pr):
        content = pr['function handle']
        if 'name' in content:
            return FunHandle(name=self.visit(content['name']))
        else:
            if 'argument list' in content.keys():
                the_args = self._convert_list(content['argument list'])
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


    def visit_funcall_or_id(self, pr):
#        pdb.set_trace()
        content = pr['funcall or id']
        name = content[0]
        if matlab_function_or_command(name):
            return FunCall(name=Identifier(name=name), args=[])
        else:
            return Identifier(name=name)


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
        return TryCatch(body=the_body, catch_var=the_var, catch_body=the_catch_body)


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
        return [self._convert_list(row['subscript list']) for row in rowlist]


# NodeTransformer
#
# Helper class that walks down a MatlabNode tree and simultaneously performs
# several jobs:
#
#  1) Tries to infer the whether each object it encounters is a variable or
#     a function.
#
#  2) Saves kind information about identifiers it encounters.
#
#  3) Converts certain classes from one type to another. This is used to do
#     things like convert ambiguous cases, like something that could be
#     either a function call or an array reference, to more specific classes
#     of objects if we have figured out what those objects should be.

class NodeTransformer(MatlabNodeVisitor):
    def __init__(self, parser):
        self._parser = parser


    def visit_list(self, node):
        return [self.visit(item) for item in node]


    def visit_FunDef(self, node):
        # Since we know this to be a function, we record its type as such.
        # Make sure to record it in the parent's context -- that's why this
        # is done before a context is pushed in the next step below.
        self._parser._save_type(node.name, 'function')

        # Push the new function context.
        self._parser._push_context(node.context)

        # Record inferred type info about the input and output parameters.
        # The type info applies *inside* the function.
        if node.output:
            for var in node.output:
                # The output parameter names are variables inside the
                # context of the function definition.
                if isinstance(var, Identifier):
                    self._parser._save_type(var.name, 'variable')
        if node.parameters:
            # We later correlate the arguments with calls to this function,
            # to figure out whether any of the arguments are known to be
            # function handles.  If they're not, we assume they're variables.

            # First, set the default as being variables.
            for param in node.parameters:
                if not isinstance(param, Special):
                    self._parser._save_type(param.name, 'variable')

            # Next, search through the dictionary of calls in the parent
            # context.  Did we ever see this function get called directly?
            # If we did, examine the arguments to the call.
            fun_name = node.name.name
            num_param = len(node.parameters)
            parent_context = self._parser._context.parent
            if fun_name in parent_context.calls:
                for arglist in parent_context.calls[fun_name]:
                    if len(arglist) != num_param:
                        continue
                    for i in range(0, num_param):
                        arg = arglist[i]
                        param = node.parameters[i]
                        if not isinstance(param, Identifier):
                            continue
                        if isinstance(arg, FunHandle):
                            self._parser._save_type(param.name, 'function')
                            break

        if node.body:
            node.body = self.visit(node.body)

        self._parser._pop_context()

        return node


    def visit_Assignment(self, node):
        # Record inferred type info about the input and output parameters.
        lhs = node.lhs
        rhs = node.rhs
        if isinstance(lhs, Identifier):
            if (isinstance(rhs, FunCall) and isinstance(rhs.name, Identifier)
                and rhs.name.name == 'str2func'):
                # Special case: a function is being created using Matlab's
                # str2func(), so in fact, the thing we're assigning to should
                # be considered a function.
                self._parser._save_type(lhs.name, 'function')
            elif (isinstance(rhs, Array) or isinstance(rhs, Number)
                  or isinstance(rhs, String)):
                self._parser._save_type(lhs.name, 'variable')
        elif isinstance(lhs, ArrayRef):
            # A function call can't appear on the LHS of an assignment, so
            # we know that what we have here is a variable, not a function.
            self._parser._save_type(lhs.name, 'variable')
        elif isinstance(lhs, Array):
            # If the LHS of an assignment is a bare array, and if there
            # are bare identifiers inside the array, then they must be
            # variables and not functions (else, syntax error).
            row = lhs.rows[0]  # Can only have one row when arrays is on lhs.
            for item in row:
                if isinstance(item, Identifier):
                    self._parser._save_type(item.name, 'variable')
        return node


    def visit_ArrayOrFunCall(self, node):
        if not isinstance(node.name, Identifier):
            # FIXME: it is potentially the case that a function call is
            # nested, using the result of another reference.  In that case,
            # the name won't be an Identifier.  Currently, the code below
            # doesn't handle that case.
            return node
        the_name = node.name.name
        context = self._parser._context
        if (matlab_function_or_command(the_name) or
            self._parser._get_type(the_name, context, True) == 'function'):
            # This is a known function or command.  We can convert this
            # to a FunCall.  At this time, we also process the arguments.
            the_args = self.visit(node.args)
            node = FunCall(name=node.name, args=the_args)
        elif self._parser._get_type(the_name, context, True) == 'variable':
            # We have seen this name before, and it's not a function.  We
            # can convert this ArrayOrFunCall to an ArrayRef.  We can
            # also convert the arguments/subscripts.

            # Also, if it was previously unknown whether this name is a
            # function or array, it might have been put in the list of
            # function calls.  Remove it if so.
            if the_name in context.calls:
                context.calls.pop(the_name)

            the_args = self.visit(node.args)
            node = ArrayRef(name=node.name, args=the_args, is_cell=False)
        else:
            # Although we didn't change the type of this ArrayOrFunCall,
            # we may still be able to change some of its arguments.
            node.args = self.visit(node.args)
        return node


    def visit_ArrayRef(self, node):
        # Convert array refs that were later found out to be function calls.
        if not isinstance(node.name, Identifier):
            return node
        the_name = node.name.name
        context = self._parser._context
        if self._parser._get_type(the_name, context, True) == 'function':
            # We have seen this name before, and it's a function.  We need to
            # convert this ArrayRef to FunCall.  Also, store this as a
            # function call.  And let's not forget to convert the subscripts.
            if the_name not in context.calls:
                self._parser._save_function_call(node)
            the_args = self.visit(node.args)
            node = FunCall(name=node.name, args=the_args)
        else:
            # Although we didn't change the type of this ArrayRef, we may
            # still be able to change some of its arguments.
            node.args = self.visit(node.args)
        return node



# EntitySaver
#
# Helper class to save some types of objects into the context structure.
# This is designed to be called starting from the top of the input file.

class EntitySaver(MatlabNodeVisitor):
    def __init__(self, parser):
        self._parser = parser


    def visit_FunDef(self, node):
        # Push a new function context, so that the other methods in this
        # class work with the right context.
        self._parser._push_context(node.context)
        node.body = self.visit(node.body)
        self._parser._pop_context()
        return node


    def visit_Assignment(self, node):
        self._parser._save_assignment(node)
        return node


    def visit_ArrayOrFunCall(self, node):
        if not isinstance(node.name, Identifier):
            return node
        name = node.name.name
        found_type = self._parser._get_type(name, self._parser._context, False)
        if found_type != 'variable':
            self._parser._save_function_call(node)
        return node


    def visit_FunCall(self, node):
        self._parser._save_function_call(node)
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
    _NC_TRANSP  = Literal(".'")
    _CC_TRANSP  = Literal("'")

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

    _identifier = Word(alphas, alphanums + '_')('identifier')
    _id         = NotAny(_reserved) + _identifier
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
    # stored in _foo.  This has implications for our use of _store_stmt()
    # further below: setting a name on _bar & _biff as above causes copies of
    # _bar and _biff to be used in _foo, which means _bar and _biff never get
    # called, which means _store_stmt() is never called either.  This leads
    # to subtle and frustrating rounds of bug-chasing.
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

    # Continuations.
    #
    # This is used later in the definition of some types of statements that
    # allow continuations.  Most do not.

    _continuation  = Combine(_ELLIPSIS.leaveWhitespace() + _EOL + _SOL)

    # The 'end' keyword is special because of its many meanings.  One applies
    # when indexing arrays.  This next definition is so we can detect that.

    _end_op        = Keyword('end')('end operator')

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
    # For this to work, the next bunch of grammar objects have to be
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
    # is why whitespace appears in the next few terms.  So, if you find
    # yourself looking at these and thinking that the business involving
    # Optional(_WHITE) and so on is useless and can be removed: no, they have
    # to stay to make later definitions work.

    ParserElement.setDefaultWhitespaceChars(' \t')

    _one_sub       = Group(_COLON('colon')) | _expr_in_array
    _comma_subs    = _one_sub + ZeroOrMore(Optional(_WHITE) + _COMMA + Optional(_WHITE) + _one_sub)
    _space_subs    = _one_sub + ZeroOrMore(OneOrMore(_WHITE) + _one_sub)

    _call_args     = delimitedList(_expr)
    _opt_arglist   = Optional(_call_args('argument list'))

    # Bare matrices.  This is a cheat because it doesn't check that all the
    # element contents have the same data type.  But again, since we expect our
    # input to be valid Matlab, we don't expect to have to verify that property.

    _row_sep       = Optional(_WHITE) + _SEMI | Optional(_WHITE) + _comment.suppress() | _EOL
    _one_row       = _comma_subs('subscript list') ^ _space_subs('subscript list')
    _rows          = Group(_one_row) + ZeroOrMore(_row_sep + Optional(_WHITE) + Group(_one_row))
    _bare_array    = Group(_LBRACKET + Optional(_rows('row list')) + _RBRACKET
                             ).setResultsName('array')  # noqa

    ParserElement.setDefaultWhitespaceChars(' \t\n\r')

    # Named array references.  Note: this interacts with the definition of
    # function calls later below.  (See _funcall_or_array.)

    _array_args    = Group(_comma_subs)
    _array_access  = Group(_name
                           + _LPAR + _array_args('subscript list') + _RPAR
                          ).setResultsName('array')  # noqa

    # Cell arrays.  You can write {} by itself, but a reference has to have at
    # least one subscript: "somearray{}" is not valid.  Newlines don't
    # seem to be allowed in args to references, but a bare ':' is allowed.
    # Now the hard parts:
    # - The following parses as a cell reference:        a{1}
    # - The following parses as a function call:         a {1}
    # - The following parses as an array of 3 elements:  [a {1} a]

    _bare_cell     = Group(_LBRACE + ZeroOrMore(_rows('row list')) + _RBRACE
                             ).setResultsName('cell array')  # noqa
    _cell_args     = Group(_comma_subs)
    _cell_access   = Group(_name + _LBRACE.leaveWhitespace()
                              + _cell_args('subscript list') + _RBRACE
                             ).setResultsName('cell array')  # noqa
    _cell_array    = _cell_access | _bare_cell

    # Function handles.
    #
    # See http://mathworks.com/help/matlab/ref/function_handle.html
    # In all function arguments, you can use a bare tilde to indicate a value
    # that can be ignored.  This is not obvious from the functional
    # documentation, but it seems to be the case when I try it.  (It's the
    # case for function defs and function return values too.)

    _named_handle  = Group('@' + _name)
    _anon_handle   = Group('@' + _LPAR + _opt_arglist + _RPAR
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
                                + _DOT.leaveWhitespace()
                                + _struct_field)('struct')
    _struct_base        = Group(_simple_struct + FollowedBy(_DOT)
                                ^ _fun_handle
                                ^ _funcall_or_array
                                ^ _cell_access
                                ^ _array_access
                                ^ _id)
    _struct_access      = Group(_struct_base('struct base')
                                + _DOT.leaveWhitespace()
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
    #
    # We try to avoid mistakenly parsing an expression like "x > [1 2]" alone
    # on a line as a command-style function call.  Here it's done with a
    # negative lookahead test against many operators.  However, the list in
    # _operators is not all possible operators, on purpose: if something
    # looks like a unary operator (especially minus or logical not), we don't
    # want to fail to treat it as a possible first argument to a
    # command-style funcall.  (E.g., "print -dpng foo.png")

    _operators         = Group(_PLUS ^ _TIMES ^ _ELTIMES ^ _MLDIVIDE
                               ^ _RDIVIDE ^ _LDIVIDE ^ _MPOWER ^ _ELPOWER
                               ^ _LE ^ _GE ^ _NE ^ _LT ^ _GT ^ _EQ)
    _noncmd_arg_start  = _EQUALS | _LPAR | _operators | _delimiter | _comment
    _fun_cmd_arg       = _STRING | CharsNotIn(" ,;\t\n\r")
    _fun_cmd_arglist   = _fun_cmd_arg + ZeroOrMore(NotAny(_noncontent)
                                                   + _WHITE
                                                   + _fun_cmd_arg)
    _funcall_cmd_style = Group(_name + _WHITE + NotAny(_noncmd_arg_start)
                               + _fun_cmd_arglist('arguments')
                              ).setResultsName('command statement')

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
    # known MATLAB function.  This is done in post processing, but we tag the
    # possible cases during the initial parse by looking for _funcall_or_id
    # instead of a plain _id.  This is why the following seemingly-pointless
    # definition exists, and is used instead of using _id directly in
    # _operand_basic and other similar places later.

    _funcall_or_id = _id('funcall or id')

    # Transpose operators.  The operator must immediately follow the thing
    # being transposed, without whitespace.
    #
    # FIXME: this grammar for transpose is hacky and incomplete.  In MATLAB
    # you can actually apply transpose to full expressions, but I haven't
    # been able to write a proper grammar that doesn't lead to infinite
    # recursion.  This hacky thing is a partial solution.  The basic idea is
    # to avoid writing what would be the natural definition, namely
    # _expr.leaveWhitespace() + NotAny(_WHITE) + _transp_op('operator') and
    # replace _expr with a limited subset of allowed expressions.  The
    # specific subset and their order inside the Group() inside _trans_what
    # was determined by trial and error.  BE VERY CAREFUL about the ordering,
    # even though it is not the same as _operand_basic.  A change to the order
    # can lead to infinite recursion on some inputs.  The current order was
    # determined by trial and error to work on our various test cases.
    #
    # The part involving _paren_expr is because it turns out you don't get
    # infinite recursion for cases when the expression is inside parens, so
    # at least we can handle that much (though handling _expr completely
    # would be more correct).


    # 2016-01-23 still doesn't work for nested transposes.
    # Problem is this is a left-recursive grammar, which a simple
    # recursive-descent parser like Pyparsing can't handle.
    # http://stackoverflow.com/a/14420388/743730
    # Need to turn it around somehow.
    # Also try using Combine(...)


    _paren_expr    = _LPAR + Optional(_WHITE) + _expr \
                     + Optional(_WHITE) + _RPAR
    _transp_op     = _NC_TRANSP ^ _CC_TRANSP
    _transp_what   = _paren_expr ^ Group(_funcall_or_array
                                         | _cell_array
                                         | _bare_array
                                         | _array_access
                                         | _fun_handle
                                         | _funcall_or_id
                                         | _NUMBER)
    _transpose     = Group(_transp_what('operand').leaveWhitespace()
                           + _transp_op('operator').leaveWhitespace()
                          ).setResultsName('transpose')  # noqa

    # And now, general expressions and operators.  Here we have a bit of
    # ugliness, in that we need to allow the keyword 'end' in expressions
    # that involve array subscripts, but 'end' is generally not permitted
    # in other expression contexts.  (There's some question about what is
    # permitted -- see http://stackoverflow.com/a/23017087/743730).  We
    # allow it everywhere, and again rely on the principle that the input is
    # already valid MATLAB, so it won't contain 'end' where it's not allowed.

    _operand_basic = _transpose          \
                     | _funcall_or_array \
                     | _struct_access    \
                     | _array_access     \
                     | _cell_array       \
                     | _bare_array       \
                     | _fun_handle       \
                     | _funcall_or_id    \
                     | _NUMBER           \
                     | _STRING

    _operand       = Group(_operand_basic)

    # The operator precedence rules in Matlab are listed here:
    # http://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html

    # Note: colon operator for 3 arguments is not implemented with the code
    # below, because I couldn't seem to make the infixNotation ternary case
    # work.  So, here the colon op is defined as binary, and then it's fixed
    # up in post-processing in NodeTransformer.

    _uplusminusneg = _UMINUS ^ _UPLUS ^ _UNOT
    _plusminus     = _PLUS ^ _MINUS
    _timesdiv      = _TIMES ^ _ELTIMES ^ _MRDIVIDE ^ _MLDIVIDE ^ _RDIVIDE ^ _LDIVIDE
    _power         = _MPOWER ^ _ELPOWER
    _logical_op    = _LE ^ _GE ^ _NE ^ _LT ^ _GT ^ _EQ
    _colon_op      = _COLON('colon operator')

    _expr        <<= infixNotation(_operand, [
        (Group(_power),         2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_uplusminusneg), 1, opAssoc.RIGHT),
        (Group(_timesdiv),      2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_plusminus),     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_colon_op),      2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_logical_op),    2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_AND),           2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_OR),            2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_AND),     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_OR),      2, opAssoc.LEFT, makeLRlike(2)),
    ])

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
    # The only solution I have found so far is to define the expression
    # grammar differently for the case of array contents.  This is the reason
    # for _expr_in_array below; this version of _expr deals with whitespace
    # explicitly.  The definitions of arrays and their subscripts earlier in
    # this file have explicit whitespace definitions in them, which wouldn't
    # be necessary except for the fact that _operand_in_array below uses
    # leaveWhitespace() to cause whitespace to be significant.

    _plusminus_array = (OneOrMore(_WHITE) + (_PLUS ^ _MINUS).leaveWhitespace() + OneOrMore(_WHITE)) \
                       | (NotAny(_WHITE) + (_PLUS ^ _MINUS).leaveWhitespace())

    _operand_in_array = Group(_end_op | _operand_basic).leaveWhitespace()

    _expr_in_array <<= infixNotation(_operand_in_array, [
        (Group(_uplusminusneg), 1, opAssoc.RIGHT),
        (Group(_power),         2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_timesdiv),      2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_plusminus_array),     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_colon_op),      2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_logical_op),    2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_AND),           2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_OR),            2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_AND),     2, opAssoc.LEFT, makeLRlike(2)),
        (Group(_SHORT_OR),      2, opAssoc.LEFT, makeLRlike(2)),
    ])

    # Assignments.
    #
    # We tag the LHS with 'lhs' whether it's a single variable or an array,
    # because we can distinguish the cases by examining the parsed object.

    _lhs_var        = Group(_id)
    _simple_assign  = Group(_lhs_var('lhs') + _EQUALS + _expr('rhs'))
    _lhs_array      = Group(_struct_access | _array_access | _bare_array | _cell_array)
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

    _single_expr    = _expr('expression') + FollowedBy(_noncontent)
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

    # Statements.
    #
    # The definition of _stmt puts all statement types except _shell_cmd
    # together and sets them up to allow ellipsis continuations.
    # (Continuations don't work in shell commands.)

    _stmt = Group(_control_stmt
                  | _scope_stmt
                  | _assignment
                  | _funcall_cmd_style
                  | _standalone_expr)
    _stmt.ignore(_continuation)

    # Statement lists are almost the full _matlab_syntax, except that
    # they don't include function definitions.

    _stmt_list <<= ZeroOrMore(_stmt ^ _shell_cmd ^ _noncontent)

    # Function definitions.
    #
    # When a function returns multiple values and the LHS is an array
    # expression in square brackets, a bare tilde can be put in place of an
    # argument value to indicate that the value is to be ignored.  Function
    # definitions also allow ellipsis continuations.

    _matlab_syntax  = Forward()

    _single_value   = Group(_id) | Group(_TILDE)
    _comma_values   = delimitedList(_single_value)
    _space_values   = OneOrMore(_single_value)
    _multi_values   = _LBRACKET + (_comma_values ^ _space_values) + _RBRACKET
    _fun_outputs    = Group(_multi_values) | Group(_single_value)
    _fun_params     = delimitedList(Group(_TILDE) | Group(_id))
    _fun_paramslist = _LPAR + Optional(_fun_params) + _RPAR
    _fun_def        = Group(_FUNCTION
                            + Optional(_fun_outputs('output list') + _EQUALS())
                            + _name
                            + Optional(_fun_paramslist('parameter list'))
                            + Group(_matlab_syntax)('body')
                            + Optional(_END)
                           ).setResultsName('function definition')

    _fun_def_stmt   = Group(_fun_def)
    _fun_def_stmt.ignore(_continuation)

    # The overall MATLAB syntax definition.
    #
    # This fails to encode the following rules of MATLAB syntax, but once
    # again we fall back on the expectation that the input already conforms
    # to valid syntax:
    #
    # 1) In real MATLAB, if a function definition exists in a file that has
    #    other statements, then the function definition must have an explicit
    #    'end'.  If the function definition is the only thing in the file
    #    (aside from comments), then the 'end' may be omitted.  Our syntax
    #    always only has it as optional.

    _matlab_syntax <<= ZeroOrMore(_fun_def_stmt ^ _stmt ^ _shell_cmd ^ _noncontent)


    # Generator for final MatlabNode-based output representation.
    #
    # The following post-processes the ParseResults-based output from PyParsing
    # and creates our format consisting of MatlabContext and MatlabNode.
    # .........................................................................

    def _generate_nodes_and_contexts(self, pr):
        # Start by creating a context for the overall input.
        self._push_context(MatlabContext(topmost=True))

        # 1st pass: visit ParseResults items, translate them to MatlabNodes,
        # and create contexts for anyfunction definitions encountered.
        nodes = [ParseResultsTransformer(self).visit(item) for item in pr]

        # 2nd pass: infer the types of objects where possible, and transform
        # some classes into others to overcome limitations in our initial parse.
        nodes = [NodeTransformer(self).visit(node) for node in nodes]

        # 3rd pass: store more constructs in our context structure, now
        # that we have a context structure for the whole file.
        nodes = [EntitySaver(self).visit(node) for node in nodes]

        # 4th pass: another node transformation pass.  That's twice we do
        # this.  Yes, it's inefficient.  Maybe a future update can figure out
        # how to avoid it.  The problem this solves is that we can't tell
        # what some things are until we see how they're used, and we don't
        # have that information until we've seen the whole file.  This is
        # approach is a sledgehammer, but it does it.
        nodes = [NodeTransformer(self).visit(node) for node in nodes]

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
        # Don't pop top-most context.
        if self._context.parent and not self._context.topmost:
            self._context = self._context.parent


    def _save_function_definition(self, node):
        # FIXME function "names" might be more than identifiers, such as a
        # cell array or structure reference.  This doesn't handle that.
        the_name = node.name.name       # Node.name is an Identifier.
        newcontext = MatlabContext(name=the_name, parent=self._context,
                                   parameters=node.parameters,
                                   returns=node.output, pr=None, topmost=False)
        self._context.functions[the_name] = newcontext
        return newcontext


    def _save_assignment(self, node):
        key = MatlabGrammar.make_key(node.lhs)
        self._context.assignments[key] = node.rhs


    def _save_function_call(self, node):
        key = MatlabGrammar.make_key(node.name)
        # Save each call as a list of the arguments to the call.
        # This will thus be a list of lists.
        if key not in self._context.calls:
            self._context.calls[key] = [node.args]
        else:
            self._context.calls[key].append(node.args)


    def _save_type(self, thing, type):
        key = MatlabGrammar.make_key(thing)
        self._context.types[key] = type


    def _get_type(self, thing, context, recursive=False):
        key = MatlabGrammar.make_key(thing)
        if key in context.types:
            return context.types[key]
        elif recursive and hasattr(context, 'parent') and context.parent:
            return self._get_type(key, context.parent, True)
        else:
            return None


    # Debugging.
    # .........................................................................

    # Name each grammar object after itself, so that when PyParsing prints
    # debugging output, it uses the name rather than a generic regexp term.

    _to_name = [ _AND, _CC_TRANSP, _COLON, _COMMA, _DOT, _ELLIPSIS,
                 _ELPOWER, _ELTIMES, _EOL, _EQ, _EQUALS, _EXPONENT, _FLOAT,
                 _GE, _GT, _INTEGER, _LBRACE, _LBRACKET, _LDIVIDE, _LE,
                 _LPAR, _LT, _MINUS, _MLDIVIDE, _MPOWER, _MRDIVIDE,
                 _NC_TRANSP, _NE, _NUMBER, _OR, _PLUS, _RBRACE, _RBRACKET,
                 _RDIVIDE, _RPAR, _SEMI, _SHORT_AND, _SHORT_OR, _SOL,
                 _STRING, _TILDE, _TIMES, _UMINUS, _UNOT, _UPLUS, _WHITE,
                 _anon_handle, _array_access, _array_args, _assignment,
                 _bare_array, _bare_cell, _block_c_end, _block_c_start,
                 _block_comment, _body, _break_stmt, _call_args, _catch_body,
                 _catch_term, _catch_var, _cell_access, _cell_args,
                 _cell_array, _colon_op, _comma_subs, _comma_values,
                 _comment, _continuation, _continue_stmt, _control_stmt,
                 _delimiter, _else_stmt, _elseif_stmt, _end_op, _expr,
                 _expr_in_array, _for_stmt, _for_version1, _for_version2,
                 _fun_access, _fun_cmd_arg, _fun_cmd_arglist,
                 _funcall_cmd_style, _fun_def_stmt, _funcall_or_id,
                 _fun_handle, _fun_outputs, _fun_params, _fun_paramslist,
                 _funcall_or_array, _id, _identifier, _if_stmt, _lhs_array,
                 _lhs_var, _line_c_start, _line_comment, _logical_op,
                 _loop_var, _matlab_syntax, _multi_values, _named_handle,
                 _noncmd_arg_start, _noncontent, _one_row, _one_sub,
                 _operand, _operand_basic, _operand_in_array, _opt_arglist,
                 _other_assign, _paren_expr, _plusminus, _power, _reserved,
                 _return_stmt, _row_sep, _rows, _scope_args, _scope_stmt,
                 _scope_type, _scope_var_list, _shell_cmd, _shell_cmd_cmd,
                 _simple_assign, _simple_struct, _simple_struct_base,
                 _single_expr, _single_value, _space_subs, _space_values,
                 _stmt, _stmt_list, _struct_access, _struct_base,
                 _standalone_expr, _struct_field, _switch_other,
                 _switch_stmt, _timesdiv,
                 _transp_op, _transp_what, _transpose, _try_stmt,
                 _uplusminusneg, _while_stmt ]

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

    _to_print_debug = _to_name

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


    def _reset(self):
        self._context = None
        self._push_context(MatlabContext(topmost=True))


    # External interfaces.
    # .........................................................................

    def parse_string(self, input, print_results=False, print_debug=False,
                     fail_soft=False):
        '''Parses MATLAB input and returns an a MatlabContext object.

        :param print_debug: print complete parsing debug output.
        :param print_results: print the internal presentation of the results.
        :param fail_soft: don't raise an exception if parsing fails.

        Warning: print_debug produces *a lot* of output.  Don't use it on
        anything more than a few lines of input.
        '''
        self._reset()
        try:
            self._print_debug(print_debug)
            pr = self._matlab_syntax.parseString(input, parseAll=True)
            top_context = self._generate_nodes_and_contexts(pr)
            if print_results:
                self.print_parse_results(top_context)
            return top_context
        except ParseException as err:
            msg = "Error: {0}".format(err)
            if fail_soft:
                print(msg)
                return None
            else:
                raise err


    def parse_file(self, path, print_results=False, print_debug=False,
                   fail_soft=False):
        '''Parses the MATLAB contained in `file` and returns a MatlabContext.
        object This is essentially identical to MatlabGrammar.parse_string()
        but does the work of opening and closing the `file`.

        :param print_debug: print complete parsing debug output.
        :param print_results: print the internal presentation of the results.
        :param fail_soft: don't raise an exception if parsing fails.

        Warning: print_debug produces *a lot* of output.  Don't use it on
        anything more than a few lines of input.
        '''
        self._reset()
        try:
            file = open(path, 'r')
            contents = file.read()
            self._print_debug(print_debug)
            pr = self._matlab_syntax.parseString(contents, parseAll=True)
            top_context = self._generate_nodes_and_contexts(pr)
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
                raise err


    def print_parse_results(self, results, print_raw=False):
        '''Prints a representation of the parsed output given in `results`.
        This is intended for debugging purposes.  If `print_raw` is True,
        prints the underlying Python objects of the representation.  The
        objects in the output are valid Python objects, and in theory could
        be used to recreate the input or or less exactly.

        If `print_raw` is False (the default), prints the output in a
        slightly more human-readable form.
        '''
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
    def make_key(thing):
        '''Turns a parsed object like an array into a canonical text-string
        form, for use as a key in dictionaries such as MatlabContext.assignments.
        '''
        def row_to_string(row):
            list = [MatlabGrammar.make_key(item) for item in row]
            return ','.join(list)

        if isinstance(thing, str):
            return thing
        elif isinstance(thing, Primitive):
            return str(thing.value)
        elif isinstance(thing, Identifier):
            return str(thing.name)
        elif isinstance(thing, FunCall) or isinstance(thing, ArrayOrFunCall):
            base = MatlabGrammar.make_key(thing.name)
            return base + '(' + row_to_string(thing.args) + ')'
        elif isinstance(thing, ArrayRef):
            base  = MatlabGrammar.make_key(thing.name)
            left  = '{' if thing.is_cell else '('
            right = '}' if thing.is_cell else ')'
            return base + left + row_to_string(thing.args) + right
        elif isinstance(thing, StructRef):
            base = MatlabGrammar.make_key(thing.name)
            return base + '.' + MatlabGrammar.make_key(thing.field)
        elif isinstance(thing, Array):
            rowlist = [row_to_string(row) for row in thing.rows]
            return '[' + ';'.join(rowlist) + ']'
        elif isinstance(thing, Operator):
            if isinstance(thing, UnaryOp):
                return thing.op + MatlabGrammar.make_key(thing.operand)
            elif isinstance(thing, BinaryOp):
                left = MatlabGrammar.make_key(thing.left)
                right = MatlabGrammar.make_key(thing.right)
                return left + thing.op + right
            elif isinstance(thing, ColonOp):
                left = MatlabGrammar.make_key(thing.left)
                right = MatlabGrammar.make_key(thing.right)
                if thing.middle:
                    middle = MatlabGrammar.make_key(thing.middle)
                    return left + ':' + middle + ':' + right
                else:
                    return left + ':' + right
            elif isinstance(thing, Transpose):
                return MatlabGrammar.make_key(thing.operand) + thing.op
        elif isinstance(thing, FunHandle):
            return str(thing)
        elif isinstance(thing, AnonFun):
            arg_list = row_to_string(thing.args)
            body = MatlabGrammar.make_key(thing.body)
            return '@(' + arg_list + ')' + body
        elif isinstance(thing, Comment) or isinstance(thing, FunDef) \
             or isinstance(thing, Command):
            # No reason for make_key called for these things, but must catch
            # random mayhem before falling through to the final case.
            return None
        elif isinstance(thing, list):
            the_list = [MatlabGrammar.make_formula(term, False) for term in thing]
            return '(' + ''.join(the_list) + ')'
        else:
            # Something must be wrong if we get here.  Unclear what to do.
            return None


    @staticmethod
    def make_formula(thing, spaces=True, parens=True, atrans=None):
        '''Converted a mathematical expression into libSBML-style string form.
        The default behavior is to put spaces between terms and operators; if
        the optional flag 'spaces' is False, then no spaces are introduced.
        The default between is also to surround the expression with
        parentheses but if the optional flag 'parens' is False, the outermost
        parentheses (but not other parentheses) are omitted.  Finally, if
        given a function for parameter 'atrans' (default: none), it will
        call that function when it encounters array references.  The function
        will be given one argument, the array object, and should return a
        text string corresponding to the value to be used in place of the
        array.  If no 'atrans' is given, the default behavior is to render
        arrays like they would appear in Matlab text: e.g., "foo(2,3)".
        '''
        def compose(name, args, delimiters=None):
            list = [MatlabGrammar.make_formula(arg, spaces, parens, atrans)
                    for arg in args]
            sep = ' ' if spaces else ''
            front = name if name else ''
            left = delimiters[0] if delimiters else ''
            right = delimiters[1] if delimiters else ''
            return front + left + sep.join(list) + right

        if isinstance(thing, str):
            return thing
        elif isinstance(thing, Primitive):
            return str(thing.value)
        elif isinstance(thing, Identifier):
            return str(thing.name)
        elif isinstance(thing, ArrayRef) or isinstance(thing, ArrayOrFunCall):
            if atrans:
                return atrans(thing)
            else:
                return compose(thing.name.name, thing.args, '()')
        elif isinstance(thing, FunCall):
            return compose(thing.name.name, thing.args, '()')
        elif isinstance(thing, Array):
            return compose(None, thing.rows, '[]')
        elif isinstance(thing, StructRef) \
             or isinstance(thing, AnonFun) \
             or isinstance(thing, FunHandle) \
             or isinstance(thing, Operator):
            return MatlabGrammar.make_key(thing)
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
