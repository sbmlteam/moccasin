#!/usr/bin/env python

# This version tries to extract the comments and store them in a way
# that associates them with a statement.

import sys
from pyparsing import (alphas, alphanums, restOfLine, srange, nums, Regex,
                       ParseException, QuotedString, Suppress, Word, Group,
                       OneOrMore, ZeroOrMore, Keyword, Literal, Combine,
                       lineEnd, traceParseAction)

# Accumulators for comments and assignments.

variables = {}
comments  = []

def store_assignment(tokens):
    # This gets called once for every matching line.
    # Tokens will be a list; the first element will be the variable.
    # For this simple test, we just create a dictionary keyed by the variable.
    global variables
    variables[tokens[0]] = tokens[1:]

def store_comment(tokens):
    global comments
    # Append here ends up mashing all the inputs into the 1st object in the list.
    # For the life of me I can't see what I'm doing wrong.  Forget it for now.
    # comments.append(tokens)
    print tokens

# Set up the parser.

commentStart = Suppress('%')

COMMENT    = commentStart + restOfLine
COMMENT.addParseAction(store_comment)

EQUALS     = Suppress('=')
RHS        = Word(nums) | Combine(Word(nums) + COMMENT) | COMMENT

ASSIGNMENT = Word(alphanums) + EQUALS + RHS
ASSIGNMENT.setParseAction(store_assignment)

GRAMMAR    = ZeroOrMore(ASSIGNMENT | COMMENT)

# Drivers.

def parse_string(str):
    comments = []
    result = GRAMMAR.parseString(str, parseAll=True)
    return result

def parse_file(filename):
    result = GRAMMAR.parseFile(filename)
    return result

# Direct run interface

if __name__ == '__main__':
    try:
        parse_string("""
% comment 1
z = 3
% comment 2
x = % comment 3
y = % another comment
""")

        # filename = open(sys.argv[1], 'r')
        # parse_file(filename)

        # print "-"*70
        # print "comments:"
        # print comments
        # print "-"*70
        # print "variables:"
        # print variables
    except ParseException as err:
        print("parse error: {0}".format(err))

