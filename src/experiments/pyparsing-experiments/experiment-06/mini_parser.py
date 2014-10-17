#!/usr/bin/env python

# This version deals with "..." continuations across lines.  It does this
# by marking "..."+newline as something to be ignored.
#
# I tried using
#    ParserElement.setDefaultWhitespaceChars(' \t\r')
# and complicated rules with a definition of EOL, but the problem then was
# joining expressions broken across lines.  It was simpler to just have it
# ignore "..." as if they weren't there.

import sys, math, operator
from pyparsing import *

sys.path.append('../common')
from moccasin_utilities import *


# Accumulators for comments and assignments.

assignments      = {}
comments         = []
expression_stack = []


def init_globals():
    global assignments
    global comments
    global expression_stack
    assignments      = {}
    comments         = []
    expression_stack = []


def pushFirst(strg, loc, toks):
    global expression_stack
    expression_stack.append(toks[0])


def pushUMinus(strg, loc, toks):
    global expression_stack
    if toks and toks[0]=='-':
        expression_stack.append( 'unary -' )


@parse_debug_helper
def store_assignment(tokens):
    # This gets called once for every matching line.
    # Tokens will be a list; the first element will be the variable.
    # For this simple test, we just create a dictionary keyed by the variable.
    global assignments
    global expression_stack
    assignments[tokens[0]] = eval_stack(expression_stack)
    expression_stack = []


@parse_debug_helper
def store_comment(tokens):
    global comments
    # Append here ends up mashing all the inputs into the 1st object in the list.
    # For the life of me I can't see what I'm doing wrong.  Forget it for now.
    # comments.append(tokens)
    print tokens


# Map operator symbols to corresponding arithmetic operations.

epsilon = 1e-12

opn = { "+" : operator.add,
        "-" : operator.sub,
        "*" : operator.mul,
        "/" : operator.truediv,
        "^" : operator.pow }

fn  = { "sin" : math.sin,
        "cos" : math.cos,
        "tan" : math.tan,
        "abs" : abs,
        "trunc" : lambda a: int(a),
        "round" : round,
        "sgn" : lambda a: abs(a)>epsilon and cmp(a,0) or 0}

def eval_stack(stack):
    op = stack.pop()
    if op == 'unary -':
        return -eval_stack( stack )
    if op in "+-*/^":
        op2 = eval_stack( stack )
        op1 = eval_stack( stack )
        return opn[op]( op1, op2 )
    elif op == "pi":
        return math.pi # 3.1415926535
    elif op == "E":
        return math.e  # 2.718281828
    elif op in fn:
        return fn[op]( eval_stack( stack ) )
    elif op[0].isalpha():
        return 0
    else:
        return float( op )


# Set up the parser.

EOL           = LineEnd().suppress()

ELLIPSIS      = Literal('...')
COMMENTSTART  = Suppress('%')

CONTINUATION  = (ELLIPSIS.leaveWhitespace() + EOL).suppress()

COMMENT       = COMMENTSTART + restOfLine
COMMENT.addParseAction(store_comment)

INTEGER       = Word("+-" + nums, nums)
#INTEGER.setParseAction(lambda tokens: int(tokens[0]))

FLOAT         = Regex(r'[+-]((\d+(\.\d*)?)|\.\d+)([EeDd][+-]?\d+)?')
#FLOAT.setParseAction(lambda tokens: float(re.sub('[dD]', 'e', tokens[0])))

NUMBER        = INTEGER | FLOAT

IDENTIFIER    = Word(alphas, alphanums + '_') # [a-zA-Z][_a-zA-Z0-9]*

PLUS          = Literal( "+" )
MINUS         = Literal( "-" )
MULT          = Literal( "*" )
DIV           = Literal( "/" )
EXPOP         = Literal( "^" )
LPAR          = Literal( "(" ).suppress()
RPAR          = Literal( ")" ).suppress()

PI            = Literal("pi")

EQUALS        = Suppress('=')

ADDOP         = PLUS | MINUS
MULTOP        = MULT | DIV

EXPR          = Forward()
FIRST_ATOM    = ( PI | NUMBER | IDENTIFIER + LPAR + EXPR + RPAR )
FIRST_ATOM.setParseAction(pushFirst)
SECOND_ATOM   = ( LPAR + EXPR.suppress() + RPAR )
ATOM          = ( Optional("-") + FIRST_ATOM | SECOND_ATOM ).setParseAction(pushUMinus)

# by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^
# atom ]...", we get right-to-left exponents, instead of left-to-righ
# that is, 2^3^2 = 2^(3^2), not (2^3)^2.

FACTOR        = Forward()
FACTOR << ATOM + ZeroOrMore( ( EXPOP + FACTOR ).setParseAction( pushFirst ) )

TERM          = FACTOR + ZeroOrMore( ( MULTOP + FACTOR ).setParseAction( pushFirst ) )
EXPR << TERM + ZeroOrMore( ( ADDOP + TERM ).setParseAction( pushFirst ) )

RHS           = EXPR + COMMENT | EXPR
ASSIGNMENT    = IDENTIFIER + EQUALS + RHS
ASSIGNMENT.setParseAction(store_assignment)

CONTENT       = ASSIGNMENT | COMMENT

GRAMMAR       = ZeroOrMore(CONTENT) + StringEnd()
GRAMMAR.ignore(CONTINUATION)

# Drivers.

def parse_string(str):
    init_globals()
    result = GRAMMAR.parseString(str, parseAll=True)
    return result

def parse_file(filename):
    init_globals()
    result = GRAMMAR.parseFile(filename)
    return result


# Direct run interface

if __name__ == '__main__':
    try:
        parse_string("""
% comment 1
% comment 2
z = 3
% comment 3
x = 3 % comment 4
y = 4 % another comment
w = -2 + 3
a = -2 + (3 * 2^2) + 10
b = 3 ...
+ 2
""")
        for name, value in assignments.iteritems():
            print "assign " + name + " = " + str(value)

    except ParseException as err:
        print("error: {0}".format(err))
