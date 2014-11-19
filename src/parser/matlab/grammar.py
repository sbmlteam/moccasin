#!/usr/bin/env python
#
# @file    grammar.py
# @brief   Core of the MATLAB grammar definition in PyParsing
# @author  Michael Hucka
#
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.

import sys
import pdb
from pyparsing import *
from grammar_utils import *


class MatlabGrammar:

    def __init__(self):
        self._do_print_tokens = False
        self._contexts        = []
        self._context_index   = -1


    # Context management.
    # .........................................................................

    def _create_context(self, name):
        new_context = dict()
        new_context['variables'] = dict()
        new_context['functions'] = dict()
        new_context['calls'] = dict()
        new_context['name'] = name
        return new_context


    def _push_context(self, name='(default context)'):
        self._contexts.append(self._create_context(name))
        self._context_index += 1


    def _pop_context(self):
        if self._context_index > 0:
            self._context_index -= 1


    def _get_context(self):
        if self._contexts:
            return self._contexts[self._context_index]
        else:
            return None


    def _get_all_contexts(self):
        return self._contexts


    # Grammar functions.
    # .........................................................................

    def _save_function_definition(self, name, args, output):
        context = self._get_context()
        if args:
            args = args.asList()
        if output:
            output = output.asList()
        context['functions'][name] = {'args': args, 'output': output}


    def _save_variable_definition(self, name, value):
        context = self._get_context()
        context['variables'][name] = value


    def _save_function_call(self, fname, args):
        context = self._get_context()
        context['calls'][fname] = args


    def _flatten(self, arg):
        if hasattr(arg, '__iter__'):
            sublist = ''
            if len(arg) == 1 and isinstance(arg[0], str):
                return arg[0]
            else:
                for x in arg:
                    sublist += self._flatten(x)
                return '(' + sublist + ')'
        else:
            return arg


    def _search_for(self, tag, pr):
        if not pr or not isinstance(pr, ParseResults):
            return None
        if pr['tag'] is not None and pr['tag'] == tag:
            return pr
        content_list = pr[0]
        for result in content_list:
            result = self._search_for(tag, content_list)
            if result is not None:
                return result
        return None


    def _store_stmt(self, tokens):
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
                    self._pop_context()
                elif tag == 'function definition':
                    content = stmt[0]
                    if len(content) == 2:
                        # Just a function name w/o args or return value.
                        name   = content[1]
                        args   = []
                        output = []
                    elif len(content) == 5:
                        # function y = f(x), where '=' is item 2.
                        output = content[1]
                        name = content[3]
                        args = content[4]
                    self._save_function_definition(name, args, output)
                    self._push_context(name)
                elif tag == 'variable assignment':
                    name = stmt[0]
                    rhs = stmt[1]
                    self._save_variable_definition(name, rhs)
                elif tag == 'matrix/cell/struct assignment':
                    rhs = stmt[1]
                    call_stmt = self._search_for('function call', rhs)
                    if call_stmt:
                        fname = call_stmt[0][0]
                        args = call_stmt[0][1]
                        self._save_function_call(fname, args)
                elif tag == 'function call':
                    # FIXME
                    pass
        except:
            pass


    def _tag(self, tokens, tag):
        if tokens is not None and isinstance(tokens, ParseResults):
            tokens['tag'] = tag
            # pdb.set_trace()


    def _interpret_type(self, pr):
        if 'tag' in pr.keys():
            return pr['tag']
        else:
            return None



    # Debugging helpers.
    # .........................................................................

    def _set_print_tokens(self, doprint):
        self._do_print_tokens = doprint


    def _print_tokens(self, tokens):
        # This gets called once for every matching line.
        # Tokens will be a list; the first element will be the variable.
        if self._do_print_tokens:
            print tokens


    # Start of grammar definition.
    #
    # Note: this is written in reverse order, from smallest elements to the
    # highest level parsing object, simply because Python interprets the file
    # in this order and needs each item defined before it encounters it
    # later.  However, for readabily, it's probably easiest to start at the
    # bottom and read up.

    # First, the lowest-level terminal tokens.
    # .........................................................................

    _EOL        = LineEnd().suppress()
    _SOL        = LineStart().suppress()
    _SEMI       = Literal(';').suppress()
    _COMMA      = Literal(',').suppress()
    _LPAR       = Literal("(").suppress()
    _RPAR       = Literal(")").suppress()
    _LBRACKET   = Literal('[').suppress()
    _RBRACKET   = Literal(']').suppress()
    _LBRACE     = Literal('{').suppress()
    _RBRACE     = Literal('}').suppress()
    _EQUALS     = Literal('=')
    _ELLIPSIS   = Literal('...')

    _INTEGER    = Word(nums)
    _EXPONENT   = Combine(oneOf('E e D d') + Optional(oneOf('+ -')) + Word(nums))
    _FLOAT      = (Combine(Word(nums) + Optional('.' + Word(nums)) + _EXPONENT)
                   | Combine(Word(nums) + '.' + _EXPONENT)
                   | Combine(Word(nums) + '.' + Word(nums))
                   | Combine('.' + Word(nums) + _EXPONENT)
                   | Combine('.' + Word(nums)))
    _NUMBER     = _FLOAT | _INTEGER
    _BOOLEAN    = Combine(Keyword('true') | Keyword('false'))
    _STRING     = QuotedString("'", escQuote="''")

    _BREAK      = Keyword('break')
    _CASE       = Keyword('case')
    _CATCH      = Keyword('catch')
    _CLASSDEF   = Keyword('classdef')
    _CONTINUE   = Keyword('continue')
    _ELSE       = Keyword('else')
    _ELSEIF     = Keyword('elseif')
    _END        = Keyword('end')
    _FIGURE     = Keyword('figure')
    _FOR        = Keyword('for')
    _FUNCTION   = Keyword('function')
    _GLOBAL     = Keyword('global')
    _HOLD       = Keyword('hold')
    _IF         = Keyword('if')
    _OTHERWISE  = Keyword('otherwise')
    _PARFOR     = Keyword('parfor')
    _PAUSE      = Keyword('pause')
    _PERSISTENT = Keyword('persistent')
    _RETURN     = Keyword('return')
    _SWITCH     = Keyword('switch')
    _TRY        = Keyword('try')
    _WHILE      = Keyword('while')

    _ID_BASE    = Word(alphas, alphanums + '_')

    # Grammar for expressions.
    # .........................................................................

    _expr              = Forward()

    # Some common items used more than once below

    _id_ref            = _ID_BASE.copy()

    # Bare matrices.  This is a cheat because it doesn't check that all the
    # element contents are of the same type.  But again, since we expect our
    # input to be valid Matlab, we don't expect to have to verify that property.

    _one_row           = Group(delimitedList(_expr) | OneOrMore(_expr))
    _rows              = Group(_one_row) + ZeroOrMore(_SEMI + Group(_one_row))
    _bare_matrix       = Group(_LBRACKET + ZeroOrMore(_rows) + _RBRACKET)

    # Cell arrays.  I think these are basically just heterogeneous matrices.
    # Note that you can write {} by itself, but a reference has to have at
    # least one indexing term: "somearray{}" is not valid.  Newlines don't
    # seem to be allowed in args to references, but a bare ':' is allowed.

    _bare_cell_array   = Group(_LBRACE + ZeroOrMore(_rows) + _RBRACE)

    _cell_array_args   = delimitedList(_expr | Group(':'))
    _cell_array_ref    = Group(_id_ref + _LBRACE + _cell_array_args + _RBRACE)

    # Function calls and matrix accesses look the same. We will have to
    # distinguish them at run-time by figuring out if a given identifier
    # reference refers to a function name or a matrix name.  Here I use 2
    # grammars because in the case of matrix references and cell array references
    # you can use a bare ':' in the argument list.

    _func_args         = delimitedList(_expr)
    _func_call         = Group(_id_ref + _LPAR + Group(Optional(_func_args)) + _RPAR)

    _matrix_args       = delimitedList(_expr | Group(':'))
    _matrix_ref        = Group(_id_ref + _LPAR + Optional(_matrix_args) + _RPAR)

    # Func. handles: http://www.mathworks.com/help/matlab/ref/function_handle.html

    _arg_list          = Group(delimitedList(_id_ref))
    _named_func_handle = '@' + _id_ref
    _anon_func_handle  = '@' + _LPAR + Group(Optional(_arg_list)) + _RPAR + _expr
    _func_handle       = Group(_named_func_handle | _anon_func_handle)

    # Struct array references.  This is incomplete: in Matlab, the LHS can
    # actually be a full expression that yields a struct.  Here, to avoid an
    # infinitely recursive grammar, we only allow a specific set of objects and
    # exclude a full expr.  (Doing the obvious thing, expr + "." + _id_ref, results
    # in an infinitely-recursive grammar.)

    _struct_base        = _cell_array_ref | _matrix_ref | _func_call | _func_handle | _id_ref
    _struct_ref         = Group(_struct_base + "." + _id_ref)

    # The transpose operator is a problem.  It seems you can actually apply it to
    # full expressions, as long as the expressions yield an array.  Parsing the
    # general case is hard because strings in Matlab use single quotes, so adding
    # an operator that's a single quote confuses the parser.  The following
    # approach is a hacky partial solution that only allows certain cases.

    _parenthesized_expr = _LPAR + _expr + _RPAR
    _transposables      = _matrix_ref | _id_ref | _bare_matrix | _parenthesized_expr
    _transpose          = Group(_transposables.leaveWhitespace() + "'")

    # The operator precendece rules in Matlab are listed here:
    # http://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html

    _operand            = Group(_transpose | _func_call | _matrix_ref
                                | _cell_array_ref | _struct_ref | _func_handle
                                | _bare_matrix | _bare_cell_array
                                | _id_ref | _NUMBER | _BOOLEAN | _STRING)

    _expr               << operatorPrecedence(_operand, [
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

    _cond_expr          = operatorPrecedence(_operand, [
        (oneOf('< <= > >= == ~='), 2, opAssoc.LEFT, makeLRlike(2)),
        ('&',                      2, opAssoc.LEFT, makeLRlike(2)),
        ('|',                      2, opAssoc.LEFT, makeLRlike(2)),
        ('&&',                     2, opAssoc.LEFT, makeLRlike(2)),
        ('||',                     2, opAssoc.LEFT, makeLRlike(2)),
    ])

    _assigned_id        = (_ID_BASE.copy()).setResultsName('vars', listAllMatches=True)
    _simple_assignment  = _assigned_id + _EQUALS.suppress() + _expr
    _other_assignment   = (_bare_matrix | _matrix_ref | _cell_array_ref | _struct_ref) + _EQUALS.suppress() + _expr
    _assignment         = _other_assignment | _simple_assignment

    _while_stmt         = Group(_WHILE + _cond_expr)
    _if_stmt            = Group(_IF + _cond_expr)
    _elseif_stmt        = Group(_ELSEIF + _cond_expr)
    _for_id             = _ID_BASE.copy()
    _for_stmt           = Group(_FOR + _for_id + _EQUALS + _expr)
    _switch_stmt        = Group(_SWITCH + _expr)
    _case_stmt          = Group(_CASE + _expr)
    _otherwise_stmt     = _OTHERWISE
    _try_stmt           = _TRY
    _catch_stmt         = Group(_CATCH + _id_ref)

    _control_stmt       = _while_stmt | _if_stmt | _elseif_stmt | _ELSE \
                          | _switch_stmt | _case_stmt | _otherwise_stmt \
                          | _for_stmt | _try_stmt | _catch_stmt \
                          | _CONTINUE | _BREAK | _RETURN \
                          | _GLOBAL | _PERSISTENT | _END   # noqa

    # Examples of Matlab command statements:
    #   figure
    #   pause
    #   pause on
    #   pause(n)
    #   state = pause('query')
    # The same commands take other forms, like pause(n), but those will get caught
    # by the regular function reference grammar.

    _common_commands    = _FIGURE | _PAUSE | _HOLD
    _command_stmt_arg   = Word(alphanums + "_")
    _command_stmt       = _common_commands | _id_ref + _command_stmt_arg

    _single_value       = _id_ref
    _ids_commas         = delimitedList(_single_value)
    _ids_spaces         = OneOrMore(_single_value)
    _multiple_values    = _LBRACKET + (_ids_spaces | _ids_commas) + _RBRACKET
    _function_def_name  = _ID_BASE.copy()
    _function_lhs       = Optional(Group(_multiple_values | _single_value) + _EQUALS)
    _func_args          = Optional(_LPAR + _arg_list + _RPAR)
    _function_def_stmt  = Group(_FUNCTION + _function_lhs + _function_def_name + _func_args)

    _line_comment       = Group('%' + restOfLine + _EOL)
    _block_comment      = Group('%{' + SkipTo('%}', include=True))
    _comment            = (_block_comment | _line_comment)
    _delimiter          = _COMMA | _SEMI
    _continuation       = Combine(_ELLIPSIS.leaveWhitespace() + _EOL + _SOL)
    _stmt               = Group(_function_def_stmt | _control_stmt
                                | _assignment | _command_stmt | _expr)

    _matlab_syntax      = ZeroOrMore(_stmt | _delimiter | _comment)
    _matlab_syntax.ignore(_continuation)

    # This is supposed to be for optimization, but unless I call this, the parser
    # simply never finishes parsing even simple inputs.
    _matlab_syntax.enablePackrat()


    # Annotation of grammar for debugging.
    # .........................................................................

    # This is a list of all the grammar terms defined above.
    _to_name = [_BOOLEAN, _COMMA, _ELLIPSIS, _END, _EQUALS, _EXPONENT, _FLOAT,
                _INTEGER, _LBRACE, _LBRACKET, _LPAR, _NUMBER, _RBRACE,
                _RBRACKET, _RPAR, _SEMI, _STRING, _BREAK, _CASE, _CATCH,
                _CLASSDEF, _CONTINUE, _ELSE, _ELSEIF, _END, _FIGURE, _FOR,
                _FUNCTION, _GLOBAL, _HOLD, _IF, _OTHERWISE, _PARFOR, _PAUSE,
                _PERSISTENT, _RETURN, _SWITCH, _TRY, _WHILE, _arg_list,
                _assigned_id, _assignment, _bare_cell_array, _bare_matrix,
                _block_comment, _case_stmt, _catch_stmt, _cell_array_args,
                _cell_array_ref, _command_stmt, _command_stmt_arg, _comment,
                _common_commands, _cond_expr, _continuation, _control_stmt,
                _delimiter, _elseif_stmt, _expr, _for_id, _for_stmt,
                _func_handle, _func_args, _func_call, _function_def_name,
                _function_def_stmt, _function_lhs, _id_ref, _ids_commas,
                _ids_spaces, _if_stmt, _line_comment, _matlab_syntax,
                _matrix_args, _matrix_ref, _multiple_values,
                _named_func_handle, _operand, _other_assignment,
                _otherwise_stmt, _parenthesized_expr, _rows,
                _simple_assignment, _one_row, _single_value, _stmt,
                _struct_base, _struct_ref, _switch_stmt, _transposables,
                _transpose, _try_stmt, _while_stmt]


    def _object_name(self, obj):
        """Returns the name of a given object."""
        for name, thing in MatlabGrammar.__dict__.iteritems():
            if thing is obj:
                return name


    def _init_grammar_names(self):
        map(lambda x: x.setName(self._object_name(x)), self._to_name)


    # Interpretation of elements in the output representation.
    # .........................................................................

    def _init_parse_actions(self):
        self._bare_matrix      .addParseAction(lambda x: self._tag(x, 'bare matrix'))
        self._one_row          .addParseAction(lambda x: self._tag(x, 'one row'))
        self._func_call        .addParseAction(lambda x: self._tag(x, 'function call'))
        self._func_handle      .addParseAction(lambda x: self._tag(x, 'function handle'))
        self._simple_assignment.addParseAction(lambda x: self._tag(x, 'variable assignment'))
        self._other_assignment .addParseAction(lambda x: self._tag(x, 'matrix/cell/struct assignment'))
        self._line_comment     .addParseAction(lambda x: self._tag(x, 'comment'))
        self._id_ref           .addParseAction(lambda x: self._tag(x, 'id reference'))
        self._expr             .addParseAction(lambda x: self._tag(x, 'expr'))
        self._function_def_stmt.addParseAction(lambda x: self._tag(x, 'function definition'))
        self._END              .addParseAction(lambda x: self._tag(x, 'end'))

        self._func_call        .addParseAction(self._store_stmt)
        self._stmt             .addParseAction(self._store_stmt)


    # Debugging.
    # .........................................................................

    _to_print = [_comment, _stmt]

    def _init_print_interpreted(self, do_print_interpreted):
        self._set_print_tokens(do_print_interpreted)
        map(lambda x: x.addParseAction(self._print_tokens), self._to_print)


    # Print low-level PyParsing matching by adding grammar terms to this list:
    _to_print_raw = [_func_args]

    def _init_print_raw(self):
        map(lambda x: x.setDebug(True), self._to_print_raw)


    # Instance initialization.
    # .........................................................................

    def _set_up_parser(self, do_print_interpreted):
        self._init_grammar_names()
        self._init_parse_actions()
        self._init_print_interpreted(do_print_interpreted)
        self._init_print_raw()
        self._push_context()


    # External interfaces.
    # .........................................................................

    def parse_string(self, str, print_interpreted=False):
        self._set_up_parser(print_interpreted)
        try:
            self._matlab_syntax.parseString(str, parseAll=True)
            return self._get_all_contexts()
        except ParseException as err:
            print("error: {0}".format(err))
            return None


    def print_parse_results(self, results):
        for c in results:
            print('')
            print('** context: ' + c['name'] + ' **')
            if len(c['variables']) > 0:
                print('    Variables defined in this context:')
                for name in c['variables'].keys():
                    value = c['variables'][name]
                    value_type = self._interpret_type(value)
                    if value_type == 'bare matrix':
                        rows = len(value[0])
                        print('      ' + name + ' = (matrix with ' + str(rows) + ' rows)')
                    elif value_type is None:
                        print('      ' + name + ' = ' + self._flatten(value.asList()))
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
