#!/usr/bin/env python


import sys, math, operator
from pyparsing import *

sys.path.append('../utilities')
from moccasin_utilities import *


# -----------------------------------------------------------------------------
# Parsing utilities.
# -----------------------------------------------------------------------------

def makeLRlike(numterms):
    if numterms is None:
        # None operator can only by binary op
        initlen = 2
        incr = 1
    else:
        initlen = {0:1,1:2,2:3,3:5}[numterms]
        incr = {0:1,1:1,2:2,3:4}[numterms]

    # define parse action for this number of terms,
    # to convert flat list of tokens into nested list
    def pa(s,l,t):
        t = t[0]
        if len(t) > initlen:
            ret = ParseResults(t[:initlen])
            i = initlen
            while i < len(t):
                ret = ParseResults([ret] + t[i:i+incr])
                i += incr
            return ParseResults([ret])
    return pa


def parse_string(str):
    result = MATLAB_SYNTAX.parseString(str, parseAll=True)
    return result


def parse_file(f):
    result = MATLAB_SYNTAX.parseFile(f)
    return result


# -----------------------------------------------------------------------------
# Debugging helpers.
# -----------------------------------------------------------------------------

@parse_debug_helper
def print_tokens(tokens):
    # This gets called once for every matching line.
    # Tokens will be a list; the first element will be the variable.
    tokens.pprint()


# Use tracer by attaching it as a parse action to a piece of grammar using
#   .setParseAction(tracer)

@traceParseAction
def tracer(tokens):
    return None


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

ID_BASE            = Word(alphas, alphanums + '_') # [a-zA-Z][_a-zA-Z0-9]*

INTEGER            = Word(nums)
EXPONENT           = Combine(oneOf('E e D d') + Optional(oneOf('+ -')) + Word(nums))
FLOAT              = ( Combine(Word(nums) + Optional('.' + Word(nums)) + EXPONENT)
                     | Combine(Word(nums) + '.' + EXPONENT)
                     | Combine(Word(nums) + '.' + Word(nums))
                     | Combine('.' + Word(nums) + EXPONENT)
                     | Combine('.' + Word(nums))
                    )
NUMBER             = FLOAT | INTEGER

TRUE               = Keyword('true')
FALSE              = Keyword('false')
BOOLEAN            = TRUE | FALSE

STRING             = QuotedString("'", escQuote="''")

# List of references to identifiers.  Used in function definitions.

ID_REF             = ID_BASE.copy()
ARG_LIST           = Group(delimitedList(ID_REF))

# Here begins the grammar for expressions.

EXPR               = Forward()

# Bare matrices.  This is a cheat because it doesn't check that all the
# element contents are of the same type.  But again, since we expect our
# input to be valid Matlab, we don't expect to have to verify that property.

ROW_WITH_SPACES    = OneOrMore(EXPR)
ROW_WITH_COMMAS    = delimitedList(EXPR)
ROW_WITH_SEMIS     = Optional(ROW_WITH_COMMAS | ROW_WITH_SPACES) + SEMI
ROW                = ROW_WITH_SEMIS | ROW_WITH_COMMAS | ROW_WITH_SPACES
BARE_MATRIX        = Group(LBRACKET + ZeroOrMore(ROW) + RBRACKET)

# Cell arrays.  I think these are basically just heterogeneous matrices.
# Note that you can write {} by itself, but a reference has to have at least
# one indexing term: "somearray{}" is not valid.  Cell array references don't
# seem to allow newlines in the args, but do allow a bare ':'.

CELL_ARRAY_ID      = ID_BASE.copy()
BARE_CELL_ARRAY    = Group(LBRACE + ZeroOrMore(ROW) + RBRACE)

CELL_ARRAY_ARGS    = delimitedList(EXPR | Group(':'))
CELL_ARRAY_REF     = CELL_ARRAY_ID + LBRACE + CELL_ARRAY_ARGS + RBRACE

# Function calls and matrix accesses look the same. We will have to
# distinguish them at run-time by figuring out if a given identifier
# reference refers to a function name or a matrix name.  Here I use 2
# grammars because in the case of matrix references and cell array references
# you can use a bare ':' in the argument list.

FUNCTION_ID        = ID_BASE.copy()
FUNCTION_ARGS      = delimitedList(EXPR)
FUNCTION_REF       = FUNCTION_ID + LPAR + Optional(FUNCTION_ARGS) + RPAR

MATRIX_ID          = ID_BASE.copy()
MATRIX_ARGS        = delimitedList(EXPR | Group(':'))
MATRIX_REF         = MATRIX_ID + LPAR + Optional(MATRIX_ARGS) + RPAR

# Func. handles: http://www.mathworks.com/help/matlab/ref/function_handle.html

FUNC_HANDLE_ID     = ID_BASE.copy()
NAMED_FUNC_HANDLE  = '@' + FUNC_HANDLE_ID
ANON_FUNC_HANDLE   = '@' + LPAR + Group(Optional(ARG_LIST)) + RPAR + EXPR
FUNC_HANDLE        = NAMED_FUNC_HANDLE | ANON_FUNC_HANDLE

# Struct array references.  This is incomplete: in Matlab, the LHS can
# actually be a full expression that yields a struct.  Here, to avoid an
# infinitely recursive grammar, we only allow a specific set of objects and
# exclude a full EXPR.  (Doing the obvious thing, EXPR + "." + ID_REF, results
# in an infinitely-recursive grammar.)

STRUCT_BASE        = CELL_ARRAY_REF | MATRIX_REF | FUNCTION_REF | FUNC_HANDLE | ID_REF
STRUCT_REF         = STRUCT_BASE + "." + ID_REF

# The transpose operator is a problem.  It seems you can actually apply it to
# full expressions, as long as the expressions yield an array.  Parsing the
# general case is hard because strings in Matlab use single quotes, so adding
# an operator that's a single quote confuses the parser.  The following
# approach is a hacky partial solution that only allows certain cases.

PARENTHESIZED_EXPR = LPAR + EXPR + RPAR
TRANSPOSABLES      = MATRIX_REF | ID_REF | BARE_MATRIX | PARENTHESIZED_EXPR
TRANSPOSE          = TRANSPOSABLES.leaveWhitespace() + "'"

# The operator precendece rules in Matlab are listed here:
# http://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html

OPERAND            = Group(TRANSPOSE | FUNCTION_REF | MATRIX_REF \
                           | CELL_ARRAY_REF | STRUCT_REF | ID_REF \
                           | FUNC_HANDLE | BARE_MATRIX | BARE_CELL_ARRAY \
                           | NUMBER | BOOLEAN | STRING)

EXPR               << operatorPrecedence(OPERAND, [
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

COND_EXPR          = operatorPrecedence(OPERAND, [
    (oneOf('< <= > >= == ~='), 2, opAssoc.LEFT, makeLRlike(2)),
    ('&',                      2, opAssoc.LEFT, makeLRlike(2)),
    ('|',                      2, opAssoc.LEFT, makeLRlike(2)),
    ('&&',                     2, opAssoc.LEFT, makeLRlike(2)),
    ('||',                     2, opAssoc.LEFT, makeLRlike(2)),
])

ASSIGNED_ID        = ID_BASE.copy()
SIMPLE_ASSIGNMENT  = ASSIGNED_ID + EQUALS + EXPR
OTHER_ASSIGNMENT   = (BARE_MATRIX | MATRIX_REF | CELL_ARRAY_REF | STRUCT_REF) + EQUALS + EXPR
ASSIGNMENT         = OTHER_ASSIGNMENT | SIMPLE_ASSIGNMENT

WHILE_STMT         = Group(Keyword('while') + COND_EXPR)
IF_STMT            = Group(Keyword('if') + COND_EXPR)
ELSEIF_STMT        = Group(Keyword('elseif') + COND_EXPR)
ELSE_STMT          = Keyword('else')
RETURN_STMT        = Keyword('return')
BREAK_STMT         = Keyword('break')
CONTINUE_STMT      = Keyword('continue')
GLOBAL_STMT        = Keyword('global')
PERSISTENT_STMT    = Keyword('persistent')
FOR_ID             = ID_BASE.copy()
FOR_STMT           = Group(Keyword('for') + FOR_ID + EQUALS + EXPR)
SWITCH_STMT        = Group(Keyword('switch') + EXPR)
CASE_STMT          = Group(Keyword('case') + EXPR)
OTHERWISE_STMT     = Keyword('otherwise')
TRY_STMT           = Keyword('try')
CATCH_STMT         = Group(Keyword('catch') + ID_REF)

END                = Keyword('end')

CONTROL_STMT       = WHILE_STMT | IF_STMT | ELSEIF_STMT | ELSE_STMT \
                    | SWITCH_STMT | CASE_STMT | OTHERWISE_STMT \
                    | FOR_STMT | TRY_STMT | CATCH_STMT \
                    | CONTINUE_STMT | BREAK_STMT | RETURN_STMT \
                    | GLOBAL_STMT | PERSISTENT_STMT | END

# Examples of Matlab command statements:
#   figure
#   pause
#   pause on
#   pause(n)
#   state = pause('query')
# The same commands take other forms, like pause(n), but those will get caught
# by the regular function reference grammar.

COMMON_COMMANDS    = Keyword('figure') | Keyword('pause') | Keyword('hold')
COMMAND_STMT       = COMMON_COMMANDS | ID_REF + Word(alphanums + "_")

SINGLE_VALUE       = ID_REF
IDS_WITH_COMMAS    = delimitedList(SINGLE_VALUE)
IDS_WITH_SPACES    = OneOrMore(SINGLE_VALUE)
MULTIPLE_VALUES    = LBRACKET + (IDS_WITH_SPACES | IDS_WITH_COMMAS) + RBRACKET
FUNCTION_NAME      = ID_BASE.copy()
FUNCTION_LHS       = Optional(Group(MULTIPLE_VALUES | SINGLE_VALUE) + EQUALS)
FUNCTION_ARGS      = Optional(LPAR + ARG_LIST + RPAR)
FUNCTION_DEF_STMT  = Group(Keyword('function') + FUNCTION_LHS + FUNCTION_NAME + FUNCTION_ARGS)

LINE_COMMENT       = Group('%' + restOfLine + EOL)
BLOCK_COMMENT      = Group('%{' + SkipTo('%}', include=True))
COMMENT            = (BLOCK_COMMENT | LINE_COMMENT).setParseAction(print_tokens)
DELIMITER          = COMMA | SEMI
CONTINUATION       = Combine(ELLIPSIS.leaveWhitespace() + EOL + EOS)
STMT               = (FUNCTION_DEF_STMT | CONTROL_STMT | ASSIGNMENT | COMMAND_STMT | EXPR).setParseAction(print_tokens)

MATLAB_SYNTAX      = ZeroOrMore(STMT | DELIMITER | COMMENT)
MATLAB_SYNTAX.ignore(CONTINUATION)

# This is supposed to be for optimization, but unless I call this, the parser
# simply never finishes parsing even simple inputs.
MATLAB_SYNTAX.enablePackrat()


# -----------------------------------------------------------------------------
# Direct run interface
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    file = open(sys.argv[1], 'r')
    print "----- input " + "-"*66
    contents = file.read()
    print contents
    print "----- output " + "-"*65
    try:
        parse_string(contents)
    except ParseException as err:
        print("error: {0}".format(err))
