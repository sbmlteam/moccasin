#!/usr/bin/env python
#
# @file    matlab_parser.py
# @brief   MATLAB parser
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#     1. California Institute of Technology, Pasadena, CA, USA
#     2. Mount Sinai School of Medicine, New York, NY, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

import sys
import math
import operator
import pdb
from pyparsing import *

sys.path.append('../utilities')
sys.path.append('../../utilities')
from moccasin_utilities import *


# -----------------------------------------------------------------------------
# Global variables.
# -----------------------------------------------------------------------------

contexts = []
context_index = -1
print_tokens = False


# -----------------------------------------------------------------------------
# Top-level call interfaces.
# -----------------------------------------------------------------------------

def parse_matlab_string(str, print_raw=False):
    global contexts
    global print_tokens
    push_context('(default context)')
    print_tokens = print_raw
    try:
        matlab_syntax.parseString(str, parseAll=True)
        return contexts
    except ParseException as err:
        print("error: {0}".format(err))
        return None


# Older version
def parse_string(str):
    try:
        return matlab_syntax.parseString(str, parseAll=True)
    except ParseException as err:
        print("error: {0}".format(err))
        return None


# -----------------------------------------------------------------------------
# Parsing utilities.
# -----------------------------------------------------------------------------

def makeLRlike(numterms):
    if numterms is None:
        # None operator can only by binary op
        initlen = 2
        incr = 1
    else:
        initlen = {0: 1, 1: 2, 2: 3, 3: 5}[numterms]
        incr = {0: 1, 1: 1, 2: 2, 3: 4}[numterms]

    # define parse action for this number of terms,
    # to convert flat list of tokens into nested list
    def pa(s, l, t):
        t = t[0]
        if len(t) > initlen:
            ret = ParseResults(t[:initlen])
            i = initlen
            while i < len(t):
                ret = ParseResults([ret] + t[i:i+incr])
                i += incr
            return ParseResults([ret])
    return pa


def get_context():
    global context_index
    global contexts
    if contexts:
        return contexts[context_index]
    else:
        return None


def create_context(name):
    new_context = dict()
    new_context['variables'] = dict()
    new_context['functions'] = dict()
    new_context['calls'] = dict()
    new_context['name'] = name
    return new_context


def push_context(name):
    global context_index
    global contexts
    contexts.append(create_context(name))
    context_index += 1


def pop_context():
    global context_index
    if context_index > 0:
        context_index -= 1


def tag_grammar(tokens, tag):
    if tokens is not None and isinstance(tokens, ParseResults):
        tokens['tag'] = tag
        # pdb.set_trace()


def get_tag(tokens):
    return tokens['tag']


def save_function_definition(name, args, output):
    context = get_context()
    context['functions'][name] = {'args': args.asList(),
                                  'output': output.asList()}


def save_variable_definition(name, value):
    context = get_context()
    context['variables'][name] = value


def save_function_call(fname, args):
    context = get_context()
    context['calls'][fname] = args


def search_for(tag, pr):
    if not pr or not isinstance(pr, ParseResults):
        return None
    if pr['tag'] is not None and pr['tag'] == tag:
        return pr
    content_list = pr[0]
    for result in content_list:
        result = search_for(tag, content_list)
        if result is not None:
            return result
    return None


@parse_debug_helper
def store_stmt(tokens):
    try:
        if not tokens:
            return
        if isinstance(tokens, ParseResults):
            stmt = tokens[0]
        if 'tag' not in stmt.keys():
            return
        if stmt['tag'] is not None:
            tag = stmt['tag']
            if tag == 'end':
                pop_context()
            elif tag == 'function definition':
                output = stmt[0][0]
                name = stmt[0][2]
                args = stmt[0][3]
                save_function_definition(name, args, output)
                push_context(name)
            elif tag == 'variable assignment':
                name = stmt[0]
                rhs = stmt[1]
                save_variable_definition(name, rhs)
            elif tag == 'matrix/cell/struct assignment':
                rhs = stmt[1]
                call_stmt = search_for('function call', rhs)
                if call_stmt:
                    fname = call_stmt[0][0]
                    args = call_stmt[0][1]
                    save_function_call(fname, args)
            elif tag == 'function call':
                pdb.set_trace()
    except:
        pass


def interpret_type(pr):
    if 'tag' in pr.keys():
        return pr['tag']
    else:
        return None


def flatten(arg):
    if hasattr(arg, '__iter__'):
        sublist = ''
        if len(arg) == 1 and isinstance(arg[0], str):
            return arg[0]
        else:
            for x in arg:
                sublist += flatten(x)
            return '(' + sublist + ')'
    else:
        return arg


def stringify_simple_expr(pr):
    return flatten(pr.asList())
    # return ' '.join(pr.asList())


def translate_parsed_formula(pr):
    return stringify_simple_expr(pr)


# -----------------------------------------------------------------------------
# Debugging helpers.
# -----------------------------------------------------------------------------

def print_stored_stmts():
    for c in contexts:
        print('')
        print('** context: ' + c['name'] + ' **')
        if len(c['variables']) > 0:
            print('    Variables defined in this context:')
            for name in c['variables'].keys():
                value = c['variables'][name]
                value_type = interpret_type(value)
                if value_type == 'bare matrix':
                    rows = len(value[0])
                    print('      ' + name + ' = (a matrix with ' + str(rows) + ' rows)')
                elif value_type is None:
                    print('      ' + name + ' = ' + stringify_simple_expr(value))
                else:
                    print('      ' + name)

        else:
            print('    No variables defined in this context.')
        if len(c['functions']) > 0:
            print('    Functions defined in this context:')
            for name in c['functions'].keys():
                fdict = c['functions'][name]
                args = fdict['args']
                output = fdict['output']
                print('      ' + ' '.join(output)
                      + ' = ' + name + '(' + ' '.join(args) + ')')
        else:
            print('    No functions defined in this context.')


def print_tokens(tokens):
    # This gets called once for every matching line.
    # Tokens will be a list; the first element will be the variable.
    global print_tokens
    if print_tokens:
        print tokens


# Use tracer by attaching it as a parse action to a piece of grammar using
#   .addParseAction(tracer)

@traceParseAction
def tracer(tokens):
    return None


@parse_debug_helper
def print_variables(parse_result_object):
    if parse_result_object is None:
        print("Empty parse results object?")
    else:
        results = parse_result_object.asDict()
        if 'vars' in results.keys():
            print results['vars']


# -----------------------------------------------------------------------------
# Grammar definition.
# -----------------------------------------------------------------------------

EOL                = LineEnd().suppress()
EOS                = LineStart().suppress()
SEMI               = Literal(';').suppress()
COMMA              = Literal(',').suppress()
LBRACKET           = Literal('[').suppress()
RBRACKET           = Literal(']').suppress()
LBRACE             = Literal('{').suppress()
RBRACE             = Literal('}').suppress()
LPAR               = Literal("(").suppress()
RPAR               = Literal(")").suppress()
EQUALS             = Literal('=')
ELLIPSIS           = Literal('...')

INTEGER            = Word(nums)
EXPONENT           = Combine(oneOf('E e D d') + Optional(oneOf('+ -')) + Word(nums))
FLOAT              = (Combine(Word(nums) + Optional('.' + Word(nums)) + EXPONENT)
                      | Combine(Word(nums) + '.' + EXPONENT)
                      | Combine(Word(nums) + '.' + Word(nums))
                      | Combine('.' + Word(nums) + EXPONENT)
                      | Combine('.' + Word(nums))
                      )
NUMBER             = FLOAT | INTEGER
BOOLEAN            = Combine(Keyword('true') | Keyword('false'))
STRING             = QuotedString("'", escQuote="''")

ID_BASE            = Word(alphas, alphanums + '_')

# List of references to identifiers.  Used in function definitions.

ID_REF             = ID_BASE.copy()

# Here begins the grammar for expressions.

expr               = Forward()

# Bare matrices.  This is a cheat because it doesn't check that all the
# element contents are of the same type.  But again, since we expect our
# input to be valid Matlab, we don't expect to have to verify that property.

single_row         = Group(delimitedList(expr) | OneOrMore(expr))
rows               = Group(single_row) + ZeroOrMore(SEMI + Group(single_row))
bare_matrix        = Group(LBRACKET + ZeroOrMore(rows) + RBRACKET)

# Cell arrays.  I think these are basically just heterogeneous matrices.
# Note that you can write {} by itself, but a reference has to have at least
# one indexing term: "somearray{}" is not valid.  Cell array references don't
# seem to allow newlines in the args, but do allow a bare ':'.

bare_cell_array    = Group(LBRACE + ZeroOrMore(rows) + RBRACE)

cell_array_args    = delimitedList(expr | Group(':'))
cell_array_ref     = Group(ID_REF + LBRACE + cell_array_args + RBRACE)

# Function calls and matrix accesses look the same. We will have to
# distinguish them at run-time by figuring out if a given identifier
# reference refers to a function name or a matrix name.  Here I use 2
# grammars because in the case of matrix references and cell array references
# you can use a bare ':' in the argument list.

function_args      = delimitedList(expr)
function_call      = Group(ID_REF + LPAR + Group(Optional(function_args)) + RPAR)

matrix_args        = delimitedList(expr | Group(':'))
matrix_ref         = Group(ID_REF + LPAR + Optional(matrix_args) + RPAR)

# Func. handles: http://www.mathworks.com/help/matlab/ref/function_handle.html

arg_list           = Group(delimitedList(ID_REF))
named_func_handle  = '@' + ID_REF
anon_func_handle   = '@' + LPAR + Group(Optional(arg_list)) + RPAR + expr
func_handle        = Group(named_func_handle | anon_func_handle)

# Struct array references.  This is incomplete: in Matlab, the LHS can
# actually be a full expression that yields a struct.  Here, to avoid an
# infinitely recursive grammar, we only allow a specific set of objects and
# exclude a full expr.  (Doing the obvious thing, expr + "." + ID_REF, results
# in an infinitely-recursive grammar.)

struct_base        = cell_array_ref | matrix_ref | function_call | func_handle | ID_REF
struct_ref         = Group(struct_base + "." + ID_REF)

# The transpose operator is a problem.  It seems you can actually apply it to
# full expressions, as long as the expressions yield an array.  Parsing the
# general case is hard because strings in Matlab use single quotes, so adding
# an operator that's a single quote confuses the parser.  The following
# approach is a hacky partial solution that only allows certain cases.

parenthesized_expr = LPAR + expr + RPAR
transposables      = matrix_ref | ID_REF | bare_matrix | parenthesized_expr
transpose          = Group(transposables.leaveWhitespace() + "'")

# The operator precendece rules in Matlab are listed here:
# http://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html

operand            = Group(transpose | function_call | matrix_ref
                           | cell_array_ref | struct_ref | func_handle
                           | bare_matrix | bare_cell_array
                           | ID_REF | NUMBER | BOOLEAN | STRING)

expr               << operatorPrecedence(operand, [
    (oneOf('- + ~'),            1, opAssoc.RIGHT),
    (".'",                      1, opAssoc.RIGHT),
    (oneOf(".^ ^"),             2, opAssoc.LEFT, makeLRlike(2)),
    (oneOf('* / .* ./ .\\ \\'), 2, opAssoc.LEFT, makeLRlike(2)),
    (oneOf('+ -'),              2, opAssoc.LEFT, makeLRlike(2)),
    ('::',                      3, opAssoc.LEFT),
    (':',                       2, opAssoc.LEFT, makeLRlike(2)),
    (oneOf('< <= > >= == ~='),  2, opAssoc.LEFT, makeLRlike(2)),
    ('&',                       2, opAssoc.LEFT, makeLRlike(2)),
    ('|',                       2, opAssoc.LEFT, makeLRlike(2)),
    ('&&',                      2, opAssoc.LEFT, makeLRlike(2)),
    ('||',                      2, opAssoc.LEFT, makeLRlike(2)),
])

cond_expr          = operatorPrecedence(operand, [
    (oneOf('< <= > >= == ~='), 2, opAssoc.LEFT, makeLRlike(2)),
    ('&',                      2, opAssoc.LEFT, makeLRlike(2)),
    ('|',                      2, opAssoc.LEFT, makeLRlike(2)),
    ('&&',                     2, opAssoc.LEFT, makeLRlike(2)),
    ('||',                     2, opAssoc.LEFT, makeLRlike(2)),
])

assigned_id        = (ID_BASE.copy()).setResultsName('vars', listAllMatches=True)
simple_assignment  = assigned_id + EQUALS.suppress() + expr
other_assignment   = (bare_matrix | matrix_ref | cell_array_ref | struct_ref) + EQUALS.suppress() + expr
assignment         = other_assignment | simple_assignment

END                = Keyword('end')
while_stmt         = Group(Keyword('while') + cond_expr)
if_stmt            = Group(Keyword('if') + cond_expr)
elseif_stmt        = Group(Keyword('elseif') + cond_expr)
else_stmt          = Keyword('else')
return_stmt        = Keyword('return')
break_stmt         = Keyword('break')
continue_stmt      = Keyword('continue')
global_stmt        = Keyword('global')
persistent_stmt    = Keyword('persistent')
for_id             = ID_BASE.copy()
for_stmt           = Group(Keyword('for') + for_id + EQUALS + expr)
switch_stmt        = Group(Keyword('switch') + expr)
case_stmt          = Group(Keyword('case') + expr)
otherwise_stmt     = Keyword('otherwise')
try_stmt           = Keyword('try')
catch_stmt         = Group(Keyword('catch') + ID_REF)

control_stmt       = while_stmt | if_stmt | elseif_stmt | else_stmt \
                    | switch_stmt | case_stmt | otherwise_stmt \
                    | for_stmt | try_stmt | catch_stmt \
                    | continue_stmt | break_stmt | return_stmt \
                    | global_stmt | persistent_stmt | END

# Examples of Matlab command statements:
#   figure
#   pause
#   pause on
#   pause(n)
#   state = pause('query')
# The same commands take other forms, like pause(n), but those will get caught
# by the regular function reference grammar.

common_commands    = Keyword('figure') | Keyword('pause') | Keyword('hold')
command_stmt_arg   = Word(alphanums + "_")
command_stmt       = common_commands | ID_REF + command_stmt_arg

single_value       = ID_REF
ids_with_commas    = delimitedList(single_value)
ids_with_spaces    = OneOrMore(single_value)
multiple_values    = LBRACKET + (ids_with_spaces | ids_with_commas) + RBRACKET
function_def_name  = ID_BASE.copy()
function_lhs       = Optional(Group(multiple_values | single_value) + EQUALS)
function_args      = Optional(LPAR + arg_list + RPAR)
function           = Keyword('function').suppress()
function_def_stmt  = Group(function + function_lhs + function_def_name + function_args)

line_comment       = Group('%' + restOfLine + EOL)
block_comment      = Group('%{' + SkipTo('%}', include=True))
comment            = (block_comment | line_comment).addParseAction(print_tokens)
delimiter          = COMMA | SEMI
continuation       = Combine(ELLIPSIS.leaveWhitespace() + EOL + EOS)
stmt               = Group(function_def_stmt | control_stmt | assignment | command_stmt | expr).addParseAction(print_tokens)

matlab_syntax      = ZeroOrMore(stmt | delimiter | comment)
matlab_syntax.ignore(continuation)

# This is supposed to be for optimization, but unless I call this, the parser
# simply never finishes parsing even simple inputs.
matlab_syntax.enablePackrat()


# -----------------------------------------------------------------------------
# Interpretation of elements
# -----------------------------------------------------------------------------

bare_matrix       .addParseAction(lambda x: tag_grammar(x, 'bare matrix'))
single_row        .addParseAction(lambda x: tag_grammar(x, 'single row'))
function_call     .addParseAction(lambda x: tag_grammar(x, 'function call'))
func_handle       .addParseAction(lambda x: tag_grammar(x, 'function handle'))
simple_assignment .addParseAction(lambda x: tag_grammar(x, 'variable assignment'))
other_assignment  .addParseAction(lambda x: tag_grammar(x, 'matrix/cell/struct assignment'))
line_comment      .addParseAction(lambda x: tag_grammar(x, 'comment'))
ID_REF            .addParseAction(lambda x: tag_grammar(x, 'id reference'))
expr              .addParseAction(lambda x: tag_grammar(x, 'expr'))

function_def_stmt .addParseAction(lambda x: tag_grammar(x, 'function definition'))
END               .addParseAction(lambda x: tag_grammar(x, 'end'))

function_call     .addParseAction(store_stmt)
stmt              .addParseAction(store_stmt)


# -----------------------------------------------------------------------------
# Annotation of grammar for debugging.
# -----------------------------------------------------------------------------

# This is a list of all the grammar terms defined above.

to_name = [BOOLEAN, COMMA, ELLIPSIS, END, EQUALS, EXPONENT, FLOAT, ID_REF,
           INTEGER, LBRACE, LBRACKET, LPAR, NUMBER, RBRACE, RBRACKET, RPAR,
           SEMI, STRING, arg_list, assigned_id, assignment,
           bare_cell_array, bare_matrix, block_comment, break_stmt, case_stmt,
           catch_stmt, cell_array_args, cell_array_ref, command_stmt,
           command_stmt_arg, comment, common_commands, cond_expr, continuation,
           continue_stmt, control_stmt, delimiter, else_stmt, elseif_stmt, expr,
           for_id, for_stmt, func_handle, function, function_args,
           function_args, function_call, function_def_name, function_def_stmt,
           function_lhs, global_stmt, ids_with_commas, ids_with_spaces,
           if_stmt, line_comment, matlab_syntax, matrix_args, matrix_ref,
           multiple_values, named_func_handle, operand, other_assignment,
           otherwise_stmt, parenthesized_expr, persistent_stmt, return_stmt,
           rows, simple_assignment, single_row, single_value, stmt,
           struct_base, struct_ref, switch_stmt, transposables, transpose,
           try_stmt, while_stmt]

# Function object_name() is based on http://stackoverflow.com/a/16139159/743730
# The map call below it calls PyParsing's setName() method on every object
# in the to_name list above, to set every object's name to itself.


def object_name(obj):
    """Returns the name of a given object."""
    for name, thing in globals().items():
        if thing is obj:
            return name

map(lambda x: x.setName(object_name(x)), to_name)


# -----------------------------------------------------------------------------
# Debug tracing
# -----------------------------------------------------------------------------

# Add grammar symbols to the to_trace list to turn on tracing for that symbol.
# E.g., to_trace = [bare_matrix] will trace matching for 'bare_matrix'.

to_trace = []

map(lambda x: x.setDebug(True), to_trace)


# -----------------------------------------------------------------------------
# Direct run interface, for testing.
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    debug = False
    print_interpreted = False
    arg_index = 1
    while sys.argv[arg_index] in ['-d', '-p']:
        if sys.argv[arg_index] == '-d':
            debug = True
        elif sys.argv[arg_index] == '-p':
            print_interpreted = True
        else:
            break
        arg_index += 1

    path = sys.argv[arg_index]
    file = open(path, 'r')
    print '----- file ' + path + ' ' + '-'*30
    contents = file.read()
    print contents
    print '----- raw parse results ' + '-'*50
    parse_matlab_string(contents, True)
    print ''
    if print_interpreted:
        print '----- interpreted output ' + '-'*50
        print_stored_stmts()
    if debug:
        pdb.set_trace()
