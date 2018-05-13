#!/usr/bin/env python
#
# @file    evaluateFormula.py
# @brief   Evaluate a string formula based on the parsed results
# @author  Sarah Keating
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

from __future__ import division
from decimal import *
import getopt
import math
import operator
import pdb
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)
import sys

__source__ = '''http://pyparsing.wikispaces.com/file/view/fourFn.py'''


class NumericStringParser(object):
    """
    Most of this code comes from the fourFn.py pyparsing example
    """
    def push_first(self, toks):
        self.exprStack.append(toks[0])

    def push_u_minus(self, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """

        # pattern for match a number
        # could be (+/-)(int)(.)int(e (+/-) int)
        point = Literal(".")
        e = CaselessLiteral("E")
        number = Word(nums)
        plusorminus = Literal('+') | Literal('-')
        int_num = Combine(Optional(plusorminus) + number)
        exponent = Combine(e + Optional(plusorminus) + number)
        double_num = (Combine(Optional(plusorminus) + Optional(number)
                              + Optional(point) + number) |
                      Combine(Optional(plusorminus)
                              + number + Optional(point)))
        fnumber = Combine((double_num | int_num) + Optional(exponent))

        ident = Word(alphas, alphas+nums+"_$")

        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        comma = Literal(",").suppress()
        exp = Literal("exp")
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                 (pi | e | fnumber | int_num | double_num |
                  ident+lpar+expr+rpar)
                 .setParseAction(self.push_first))
                | (Optional(oneOf("- +")) +
                 (pi | e | fnumber | int_num | double_num |
                  ident+lpar+expr+ZeroOrMore(comma+expr)+rpar)
                 .setParseAction(self.push_first))
                | Optional(oneOf("- +")) + Group(lpar+expr+rpar)
                ).setParseAction(self.push_u_minus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents,
        # instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore((expop + factor)
                                    .setParseAction(self.push_first))
        term = factor + ZeroOrMore((multop + factor)
                                   .setParseAction(self.push_first))
        expr << term + ZeroOrMore((addop + term)
                                  .setParseAction(self.push_first))
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore(addop_term) | OneOrMore(addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        # epsilon = 1e-12
        self.opn = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "^": operator.pow
        }
        self.fn = {
            "abs": abs,
            "acos": math.acos,
            "acosh": math.acosh,
            "asin": math.asin,
            "asinh": math.asinh,
            "atan": math.atan,
            "atanh": math.atanh,
            "ceil": math.ceil,
            "cos": math.cos,
            "cosh": math.cosh,
            "exp": math.exp,  # not working
            "factorial": math.factorial,
            "floor": math.floor,
            "fix": self.fix,
            "ln": math.log,
            "log": math.log,
            "log10": math.log10,
            "round": self.round,
            "sin": math.sin,
            "sinh": math.sinh,
            "sqrt": math.sqrt,
            "tan": math.tan,
            "tanh": math.tanh,
            "uplus": lambda a: a
        }
        self.bin_fn = {
            "mod": math.fmod,
            "plus": operator.add,
            "times": operator.mul,
            "minus": operator.sub,
            "power": operator.pow,
            "rem": math.fmod
        }

    def round(self, x):
        return int(round(x))

    def fix(self, x):
        return math.floor(x) if (x >= 0) else math.ceil(x)

    def evaluate_stack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluate_stack(s)
        if op in "+-*/^":
            op2 = Decimal(self.evaluate_stack(s))
            op1 = Decimal(self.evaluate_stack(s))
            return Decimal(self.opn[op](op1, op2))
        elif op == "PI":
            return Decimal(math.pi)  # 3.1415926535
        elif op == "E":
            return Decimal(math.e)   # 2.718281828
        elif op in self.fn:
            return Decimal(self.fn[op](self.evaluate_stack(s)))
        elif op in self.bin_fn:
            op2 = Decimal(self.evaluate_stack(s))
            op1 = Decimal(self.evaluate_stack(s))
            return Decimal(self.bin_fn[op](op1, op2))
        elif op[0].isalpha():
            return Decimal(0)
        else:
            return Decimal(op)

    def eval(self, num_string, parse_all=True):
        self.exprStack = []
        results = None
        try:
            results = self.bnf.parseString(num_string, parse_all)
        except Exception as err:
            print(err)

        if results is None:
            val = Decimal('NaN')
        else:
            val = self.evaluate_stack(self.exprStack[:])

        return val.normalize()


#
# The rest of this is a test harness.
#

def parse_file(path):
    with open(path,'r') as file:
        try:
            contents = file.read()
            if contents is not None and contents != '':
                formula_parser = NumericStringParser()
                return formula_parser.eval(contents)
        except Exception as e:
            print(e)
    return None


def get_filename_and_options(argv):
    """Helper function for parsing command-line arguments."""
    try:
        options, path = getopt.getopt(argv[1:], "iq")
    except:
        raise SystemExit(main.__doc__)
    if len(path) != 1 or len(options) > 2:
        raise SystemExit(main.__doc__)
    quiet = any(['-q' in y for y in options])
    interactive_pdb = any(['-i' in y for y in options])
    return path[0], quiet, interactive_pdb


def main(argv):
    """Usage: evaluate_formula.py [-i] [-q] FILENAME.m
Arguments:
  -i   (Optional) Drop into pdb as the final step
  -q   (Optional) Be quiet -- just print the output
"""
    path, quiet, interactive = get_filename_and_options(argv)
    parsed = parse_file(path)
    if quiet:
        print(parsed)
    else:
        print("--- Input file ---")
        with open(path,'r') as file:
            print(file.read())
        print("--- Parsed output ---")
        print(parsed)
        if interactive:
            pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)
