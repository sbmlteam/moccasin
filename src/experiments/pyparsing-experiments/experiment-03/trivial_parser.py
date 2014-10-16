#!/usr/bin/env python

import sys
from pyparsing import (alphas, alphanums, restOfLine, srange, nums, Regex,
                       ParseException, QuotedString, Suppress, Word,
                       OneOrMore, Keyword, Literal, Combine, lineEnd)

# Helper function to store variable assignments.

variables  = {}

def accumulate(tokens):
  var, value = tokens
  variables[var] = value

# Set up the parser.

STRING     = QuotedString("'", escQuote="''")

COMMENT    = '%' + Combine(restOfLine + lineEnd)
EQUALS     = Suppress('=')
ASSIGNMENT = Word(alphanums) + EQUALS + Combine(restOfLine + lineEnd)
ASSIGNMENT.setParseAction(accumulate)

GRAMMAR    = OneOrMore(ASSIGNMENT) | STRING
GRAMMAR.ignore(COMMENT)

# Drivers.

def parse_string(str):
    result = GRAMMAR.parseString(str, parseAll=True)
    return variables

def parse_file(filename):
    file = open(filename, 'r')
    result = GRAMMAR.parseFile(file)
    return result[0]
