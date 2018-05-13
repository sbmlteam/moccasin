#!/usr/bin/env python
#
# @file    grammar_formatter.py
# @brief   Debugging code for the ParseResults-based intermediate structure.
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

from pyparsing import ParseResults
from grammar import *


# MatlabGrammarFormatter
# .............................................................................
# This was the first approach to parsing and printing debugging output,
# before the introduction of the MatlabNode-based output representation.
# The code in the section below has been replaced by the methods that
# work on the MatlabNode-based representation.  Nevertheless, the code is
# left here because it might be useful for some debugging situations.
#
# To use this, do the following.  Assume that "pr" is a ParseResults object
# or a list of ParseResults objects.  Then do something like this:
#
#   from grammar_formatter import *
#   formatter = MatlabGrammarFormatter()
#   formatter.format(pr)
#

class MatlabGrammarFormatter(MatlabParser):
    def format(self, thing):
        return '\n'.join([self._format_pr(pr) for pr in thing])


    def _format_pr(self, pr):
        if isinstance(pr, str):
            return pr
        if not nonempty_dict(pr):
            # It's an expression.
            return self._format_expression(pr)
        key = first_key(pr)
        # Construct the function name dynamically.
        func_name = '_format_' + '_'.join(key.split())
        if func_name in MatlabGrammarFormatter.__dict__:
            return MatlabGrammarFormatter.__dict__[func_name](self, pr)
        else:
            self._warn('Internal error: no formatter for ' + str(key))


    def _format_identifier(self, pr):
        if not self._verified_pr(pr, 'identifier'):
            return
        content = pr['identifier']
        return '{{identifier: "{}"}}'.format(content)


    def _format_number(self, pr):
        if not self._verified_pr(pr, 'number'):
            return
        content = pr['number']
        return '{{number: {}}}'.format(content)


    def _format_boolean(self, pr):
        if not self._verified_pr(pr, 'boolean'):
            return
        content = pr['boolean']
        return '{{boolean: {}}}'.format(content)


    def _format_unary_operator(self, pr):
        op = 'unary op'
        op_key = first_key(pr)
        text = '{{{}: {}}}'.format(op, pr[op_key])
        return text


    def _format_binary_operator(self, pr):
        op = 'binary op'
        op_key = first_key(pr)
        text = '{{{}: {}}}'.format(op, pr[op_key])
        return text


    def _format_colon_operator(self, pr):
        return '{colon}'


    def _format_string(self, pr):
        if not self._verified_pr(pr, 'string'):
            return
        content = pr['string']
        return '{{string: "{}"}}'.format(content)


    def _format_assignment(self, pr):
        if not self._verified_pr(pr, 'assignment'):
            return
        content = pr['assignment']
        lhs = content['lhs']
        rhs = content['rhs']
        return '{{assign: {} = {}}}'.format(self._format_pr(lhs),
                                            self._format_pr(rhs))


    def _format_array_or_function(self, pr):
        if not self._verified_pr(pr, 'array or function'):
            return
        content = pr['array or function']
        name = content['name']
        args = self._help_format_simple_list(content['argument list'])
        return '{{function/array: {} ( {} )}}'.format(self._format_pr(name), args)


    def _format_array(self, pr):
        if not self._verified_pr(pr, 'array'):
            return
        content = pr['array']
        # Two kinds of array situations: a bare array, and one where we
        # managed to determine it's an array access (and not the more
        # ambiguous function call or array access).  If we have a row list,
        # it's the former; if we have an subscript list, it's the latter.
        if 'row list' in content:
            rows = self._help_format_rowlist(content['row list'])
            return '{{array: [ {} ]}}'.format(rows)
        elif 'subscript list' in content:
            name = self._format_pr(content['name'])
            subscripts = self._help_format_subscripts(content['subscript list'])
            return '{{array {}: [ {} ]}}'.format(name, subscripts)
        else:
            # No row list or subscript list => empty array.
            return '{array: [] }'


    def _format_cell_array(self, pr):
        if not self._verified_pr(pr, 'cell array'):
            return
        content = pr['cell array']
        rows = self._help_format_rowlist(content['row list'])
        if 'name' in content:
            name = content['name']
            return '{{cell array: {} [ {} ]}}'.format(self._format_pr(name), rows)
        else:
            return '{{cell array: [ {} ]}}'.format(rows)


    def _format_function_definition(self, pr):
        if not self._verified_pr(pr, 'function definition'):
            return
        content = pr['function definition']
        name = self._format_pr(content['name'])
        if 'output list' in content:
            output = self._help_format_simple_list(content['output list'])
            if len(content['output list']) > 1:
                output = '[ ' + output + ' ]'
        else:
            output = 'none'
        if 'parameter list' in content:
            param = self._help_format_simple_list(content['parameter list'])
        else:
            param = 'none'
        return '{{function definition: {} parameters ( {} ) output {}}}' \
            .format(name, param, output)


    def _format_function_handle(self, pr):
        if not self._verified_pr(pr, 'function handle'):
            return
        content = pr['function handle']
        if 'name' in content:
            name = content['name']
            return '{{function @ handle: {}}}'.format(self._format_pr(name))
        else:
            # No name => anonymous function
            arg_list = self._help_format_simple_list(content['argument list'])
            body = self._format_pr(content['function definition'])
            return '{{anon @ handle: args ( {} ) body {} }}'.format(arg_list, body)


    def _format_struct(self, pr):
        if not self._verified_pr(pr, 'struct'):
            return
        content = pr['struct']
        base = self._format_pr(content['struct base'])
        field = self._format_pr(content['field'])
        return '{{struct: {}.{} }}'.format(base, field)


    def _format_colon(self, pr):
        if not self._verified_pr(pr, 'colon'):
            return
        return '{colon}'


    def _format_transpose(self, pr):
        if not self._verified_pr(pr, 'transpose'):
            return
        content = pr['transpose']
        operand = self._format_pr(content['operand'])
        return '{{transpose: {} operator {} }}'.format(operand, content['operator'])


    def _format_shell_command(self, pr):
        if not self._verified_pr(pr, 'shell command'):
            return
        content = pr['shell command']
        body = content['command'][0]
        return '{{shell command: {}}}'.format(body)


    def _format_command_statement(self, pr):
        if not self._verified_pr(pr, 'command statement'):
            return
        content = pr['command statement']
        name = self._format_pr(content['name'])
        args = content['arguments'][0]
        return '{{command: name {} args {}}}'.format(name, args)


    def _format_comment(self, pr):
        if not self._verified_pr(pr, 'comment'):
            return
        content = pr['comment']
        return '{{comment: {}}}'.format(content[0])


    def _format_control_statement(self, pr):
        if not self._verified_pr(pr, 'control statement'):
            return
        content = pr['control statement']
        return self._format_pr(content)


    def _format_while_statement(self, pr):
        if not self._verified_pr(pr, 'while statement'):
            return
        content = pr['while statement']
        cond = self._format_pr(content['condition'])
        return '{{while stmt: {}}}'.format(cond)


    def _format_if_statement(self, pr):
        if not self._verified_pr(pr, 'if statement'):
            return
        content = pr['if statement']
        cond = self._format_pr(content['condition'])
        return '{{if stmt: {}}}'.format(cond)


    def _format_elseif_statement(self, pr):
        if not self._verified_pr(pr, 'elseif statement'):
            return
        content = pr['elseif statement']
        cond = self._format_pr(content['condition'])
        return '{{elseif stmt: {}}}'.format(cond)


    def _format_else_statement(self, pr):
        if not self._verified_pr(pr, 'else statement'):
            return
        return '{else}'


    def _format_switch_statement(self, pr):
        if not self._verified_pr(pr, 'switch statement'):
            return
        content = pr['switch statement']
        expr = self._format_pr(content['expression'])
        return '{{switch stmt: {}}}'.format(expr)


    def _format_case_statement(self, pr):
        if not self._verified_pr(pr, 'case statement'):
            return
        content = pr['case statement']
        expr = self._format_pr(content['expression'])
        return '{{case: {}}}'.format(expr)


    def _format_otherwise_statement(self, pr):
        if not self._verified_pr(pr, 'otherwise statement'):
            return
        return '{otherwise}'


    def _format_for_statement(self, pr):
        if not self._verified_pr(pr, 'for statement'):
            return
        content = pr['for statement']
        var = self._format_pr(content['loop variable'])
        exp = self._format_pr(content['expression'])
        return '{{for stmt: var {} in {}}}'.format(var, exp)


    def _format_try_statement(self, pr):
        if not self._verified_pr(pr, 'try statement'):
            return
        return '{try}'


    def _format_catch_statement(self, pr):
        if not self._verified_pr(pr, 'catch statement'):
            return
        content = pr['catch statement']
        var = self._format_pr(content['catch variable'])
        return '{{catch: var {}}}'.format(var)


    def _format_continue_statement(self, pr):
        if not self._verified_pr(pr, 'continue statement'):
            return
        return '{continue}'


    def _format_break_statement(self, pr):
        if not self._verified_pr(pr, 'break statement'):
            return
        return '{break}'


    def _format_return_statement(self, pr):
        if not self._verified_pr(pr, 'return statement'):
            return
        return '{return}'


    def _format_end_statement(self, pr):
        if not self._verified_pr(pr, 'end statement'):
            return
        return '{end}'


    def _format_tilde(self, pr):
        if not self._verified_pr(pr, 'tilde'):
            return
        return '{tilde}'


    def _format_expression(self, thing):
        return '( ' + ' '.join([self._format_pr(pr) for pr in thing]) + ' )'


    def _help_format_simple_list(self, pr):
        return ', '.join([self._format_pr(thing) for thing in pr])


    def _help_format_subscripts(self, subscripts):
        return ', '.join([self._format_pr(thing) for thing in subscripts])


    def _help_format_rowlist(self, arglist):
        last = len(arglist) - 1
        i = 1
        text = ''
        for row in arglist:
            if 'subscript list' not in row:
                self._warn('did not find "subscript list" key in ParseResults')
                return 'ERROR'
            subscripts = row['subscript list']
            text += '{{row {}: {}}}'.format(i, self._help_format_subscripts(subscripts))
            if i <= last:
                text += '; '
            i += 1
        return text


    def _warn(self, *args):
        print('WARNING: {}'.format(' '.join(args)))


    def _verified_pr(self, pr, type):
        if len(pr) > 1:
            self._warn('expected 1 ParseResults, but got {}'.format(len(pr)))
            return False
        if type not in pr:
            self._warn('ParseResults not of type {}'.format(type))
            return False
        return True
