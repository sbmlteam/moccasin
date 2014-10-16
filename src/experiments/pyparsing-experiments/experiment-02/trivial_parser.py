#!/usr/bin/env python

import sys
from pyparsing import (alphas, alphanums, restOfLine, srange, nums, Regex,
                       ParseException, QuotedString, Suppress, Word,
                       OneOrMore, Keyword, Literal, Combine, lineEnd)

# Set up the parser.

STRING     = QuotedString("'", escQuote="''")

COMMENT    = '%' + Combine(restOfLine + lineEnd)
EQUALS     = Suppress('=')
ASSIGNMENT = Word(alphanums) + EQUALS + Combine(restOfLine + lineEnd)

GRAMMAR    = OneOrMore(ASSIGNMENT) | STRING
GRAMMAR.ignore(COMMENT)

# Drivers.

def parse_string(str):
    result = GRAMMAR.parseString(str, parseAll=True)
    return result[0]

def parse_file(filename):
    file = open(filename, 'r')
    result = GRAMMAR.parseFile(file)
    return result[0]


# Direct run interface

if __name__ == '__main__':
  try:
    print parse_string("x = 123 % comment")
  except ParseException as err:
    print("parse error: {0}".format(err))

