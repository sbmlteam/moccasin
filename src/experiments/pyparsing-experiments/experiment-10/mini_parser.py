#!/usr/bin/env python

# Changes from 09:
# - argument lists to functions or matrix references
# - matrix on LHS of assignment

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


def pushFunction(strg, loc, toks):
    global expression_stack
    print('call ' + toks[0] + '(' + ', '.join(toks[1:]) + ')')
    # expression_stack.append('call ' + toks[0] + '(' + ', '.join(toks[1:]) + ')')


def printMatrixRef(strg, loc, toks):
    global expression_stack
    print('matrix ref ' + toks[0] + '(' + ', '.join(toks[1:]) + ')')


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
    # print tokens


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
    elif op.isalpha():
        if op in assignments:
            return assignments[op]
        elif op.startswith('call'):
            print op
            return 0
    else:
        return float( op )


# Set up the parser.

EOL               = LineEnd().suppress()
COMMENTSTART      = Literal('%').suppress()
SEMI              = Literal(';').suppress()
COMMA             = Literal(',').suppress()
LBRACKET          = Literal('[').suppress()
RBRACKET          = Literal(']').suppress()
ELLIPSIS          = Literal('...')

ID_BASE           = Word(alphas, alphanums + '_') # [a-zA-Z][_a-zA-Z0-9]*

INTEGER           = Word(nums)
EXPONENT          = Combine(oneOf('E e D d') + Optional(oneOf('+ -')) + Word(nums))
FLOAT             = (  Combine(Word(nums) + Optional('.' + Word(nums)) + EXPONENT)
                    | Combine(Word(nums) + '.' + EXPONENT)
                    | Combine(Word(nums) + '.' + Word(nums))
                    | Combine('.' + Word(nums) + EXPONENT)
                    | Combine('.' + Word(nums))
                   )
NUMBER            = FLOAT | INTEGER

LPAR              = Literal("(").suppress()
RPAR              = Literal(")").suppress()
EQUALS            = Literal('=').suppress()
PLUS              = Literal("+")
MINUS             = Literal("-")
MULT              = Literal("*")
DIV               = Literal("/")
EXPOP             = Literal("^")
COLON             = Literal(':')

EQEQ              = Literal('==')
LT                = Literal('<')
GT                = Literal('>')
LEQ               = Literal('<=')
GEQ               = Literal('>=')
NEQ               = Literal('~=')
LOR               = Literal('||')
LAND              = Literal('&&')

BOR               = Literal('|')
BAND              = Literal('&')
LEFTDIV           = Literal('/')
RIGHTDIV          = Literal('\\')
ETIMES            = Literal('.*')
ELEFTDIV          = Literal('./')
ERIGHTDIV         = Literal('.\\')
EEXP              = Literal('.^')

# Here begins the grammar for expressions.

EXPR              = Forward()

ROW_WITH_COMMAS   = delimitedList(EXPR)
ROW_WITH_SEMIS    = Optional(ROW_WITH_COMMAS) + SEMI
ROW_WITH_SPACES   = OneOrMore(EXPR)
ROW               = ROW_WITH_SEMIS | ROW_WITH_COMMAS | ROW_WITH_SPACES
MATRIX            = LBRACKET + ZeroOrMore(ROW) + RBRACKET

# Function calls and matrix accesses look the same. We will have to distinguish
# them at run-time by figuring out if a given identifier reference refers to
# a function name or a matrix name.  

FUNC_OR_MATRIX_ID   = ID_BASE.copy()
FUNC_OR_MATRIX_ARGS = delimitedList(EXPR)
FUNC_OR_MATRIX_REF  = (FUNC_OR_MATRIX_ID + LPAR + FUNC_OR_MATRIX_ARGS + RPAR).setParseAction(pushFunction)

ID_REF            = ID_BASE.copy()
SUB_1             = (FUNC_OR_MATRIX_REF | MATRIX | ID_REF | NUMBER ).setParseAction(pushFirst)
SUB_2             = LPAR + EXPR.suppress() + RPAR
ATOM              = (Optional("-") + SUB_1 | SUB_2).setParseAction(pushUMinus)
ADDOP             = PLUS | MINUS
MULTOP            = MULT | DIV

# By defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^
# atom ]...", we get right-to-left exponents, instead of left-to-righ
# that is, 2^3^2 should be 2^(3^2), not (2^3)^2.

FACTOR            = Forward()
FACTOR            << ATOM  + ZeroOrMore( ( EXPOP + FACTOR ).setParseAction( pushFirst ) )
TERM              = FACTOR + ZeroOrMore( ( MULTOP + FACTOR ).setParseAction( pushFirst ) )
EXPR              << TERM  + ZeroOrMore( ( ADDOP + TERM ).setParseAction( pushFirst ) )

ASSIGNED_ID       = ID_BASE.copy()
SIMPLE_ASSIGNMENT = (ASSIGNED_ID + EQUALS + EXPR).setParseAction(store_assignment)
MATRIX_ASSIGNMENT = MATRIX + EQUALS + EXPR
ASSIGNMENT        = MATRIX_ASSIGNMENT | SIMPLE_ASSIGNMENT

COMMENT           = (COMMENTSTART + restOfLine).addParseAction(store_comment)
DELIMITER         = COMMA | SEMI | COMMENT

MANY_ASSIGNMENTS  = OneOrMore( ASSIGNMENT + DELIMITER )
CONTENT           = MANY_ASSIGNMENTS | ASSIGNMENT | DELIMITER | COMMENT

GRAMMAR           = ZeroOrMore(CONTENT)

CONTINUATION      = (ELLIPSIS.leaveWhitespace() + EOL).suppress()
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
w = -2 + 3;
a = -2 + (3 * 2^2) + 10
b = 3 ...
+ 2
c = 7; d = 9; e=655
f=(55*10)-4 % yet another comment; with semicolon and ...

g = 1, h = 2,,
i = pi
j = 2 + h
k = foo(2)
m = 2/4
n = 1.1
n = 1.3e4
k = .3e3
p = [3]
q = [3, 4]
r = [44
2]
s = [55, 44;
66 77]
t = [;
8]
u = [1, 2, 3
4 5 6]
v = [9 9 9]
v = [a 9]
[a b] = [c d]
[a, b] = [c d]
[a b] = f(x)
A = [ [333 5 7] ; [2 18 10] ];
B = [ [8 ; 9 ; 16] [7 ; -2 ; -3] ];
D = f(1,2)
E = [11,22,
33,44]
""")
        for name, value in assignments.iteritems():
            print "assign " + name + " = " + str(value)

    except ParseException as err:
        print("error: {0}".format(err))
