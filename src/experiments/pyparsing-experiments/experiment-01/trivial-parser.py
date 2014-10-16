#!/usr/bin/env python

import sys
from pyparsing import (alphanums, restOfLine, Suppress, Word, OneOrMore)

# Helper function to store variable assignments.

def accumulate(tokens):
  var, value = tokens
  variables[var] = value

# Set up the parser.

variables  = {}
equals     = Suppress('=')
comment    = '#' + restOfLine
assignment = Word(alphanums) + equals + restOfLine
assignment.setParseAction(accumulate)

parser     = OneOrMore(assignment)
parser.ignore(comment)

# Run the show.

if __name__ == '__main__':
  file = open(sys.argv[1], 'r')
  try:
    parser.parseFile(file)
  except ParseException as err:
    print("parse error: {0}".format(err))
  print variables
