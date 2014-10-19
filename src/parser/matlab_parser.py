#!/usr/bin/env python


import sys, math, operator, pdb
from pyparsing import *

sys.path.append('../utilities')
sys.path.append('../../utilities')
from moccasin_utilities import *


# -----------------------------------------------------------------------------
# Global variables.
# -----------------------------------------------------------------------------

assignments      = {}
comments         = []
expression_stack = []


# -----------------------------------------------------------------------------
# Parsing utilities.
# -----------------------------------------------------------------------------

def init_globals():
    global assignments
    global comments
    global expression_stack
    assignments      = {}
    comments         = []
    expression_stack = []


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


@parse_debug_helper
def store_assignment(tokens):
    # This gets called once for every matching line.
    # Tokens will be a list; the first element will be the variable.
    # For this simple test, we just create a dictionary keyed by the variable.
    global assignments
    global expression_stack
    # if not tokens:
    #     pass
    # lhs = tokens[0]
    # if type(lhs) is str:
    #     # Simple assignment: x = something
    #     varname = tokens[0]
    #     assignments[varname] = tokens[1:]
    #     if type(tokens[2]) is ParseResults:
    #         # pdb.set_trace()
    #         print tokens[2].dump()
    # else:
    #     # LHS is more complicated, such as an array: [x,y] = something
    #     pass


def set_parse_tag(tokens, tag):
    if tokens is not None and type(tokens) is ParseResults:
        tokens['tag'] = tag


def tag_grammar(tokens, tag):
    if tokens is not None and type(tokens) is ParseResults:
        tokens['tag'] = tag
        # pdb.set_trace()


def get_parse_tag(tokens):
    return tokens['tag']


def print_assignments():
    global assignments
    for name, value in assignments.iteritems():
        print name + " -> " + str(value)


def print_variables(parse_result_object):
    if parse_result_object == None:
        print("Empty parse results object?")
    else:
        results = parse_result_object.asDict()
        if 'vars' in results.keys():
            print results['vars']


def print_called(parse_result_object):
    if parse_result_object == None:
        print("Empty parse results object?")
    else:
        results = parse_result_object.asDict()
        if 'called' in results.keys():
            print results['called']


def parse_string(str):
    init_globals()
    try:
        return MATLAB_SYNTAX.parseString(str, parseAll=True)
    except ParseException as err:
        print("error: {0}".format(err))
        return None


def parse_file(f):
    init_globals()
    try:
        return MATLAB_SYNTAX.parseFile(f)
    except ParseException as err:
        print("error: {0}".format(err))
        return None


# -----------------------------------------------------------------------------
# Debugging helpers.
# -----------------------------------------------------------------------------

@parse_debug_helper
def print_tokens(tokens):
    # This gets called once for every matching line.
    # Tokens will be a list; the first element will be the variable.
    tokens.pprint()


# Use tracer by attaching it as a parse action to a piece of grammar using
#   .addParseAction(tracer)

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

ID_BASE            = Word(alphas, alphanums + '_')

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

SINGLE_ROW         = Group(delimitedList(EXPR) | OneOrMore(EXPR))
ROWS               = Group(SINGLE_ROW) + ZeroOrMore(SEMI + Group(SINGLE_ROW))
BARE_MATRIX        = Group(LBRACKET + ZeroOrMore(ROWS) + RBRACKET)#.addParseAction(tracer)

# Cell arrays.  I think these are basically just heterogeneous matrices.
# Note that you can write {} by itself, but a reference has to have at least
# one indexing term: "somearray{}" is not valid.  Cell array references don't
# seem to allow newlines in the args, but do allow a bare ':'.

BARE_CELL_ARRAY    = Group(LBRACE + ZeroOrMore(ROWS) + RBRACE)

CELL_ARRAY_ARGS    = delimitedList(EXPR | Group(':'))
CELL_ARRAY_REF     = Group(ID_REF + LBRACE + CELL_ARRAY_ARGS + RBRACE)

# Function calls and matrix accesses look the same. We will have to
# distinguish them at run-time by figuring out if a given identifier
# reference refers to a function name or a matrix name.  Here I use 2
# grammars because in the case of matrix references and cell array references
# you can use a bare ':' in the argument list.

FUNCTION_ARGS      = delimitedList(EXPR)
FUNCTION_CALL      = Group(ID_REF + LPAR + Group(Optional(FUNCTION_ARGS)) + RPAR)

MATRIX_ARGS        = delimitedList(EXPR | Group(':'))
MATRIX_REF         = Group(ID_REF + LPAR + Optional(MATRIX_ARGS) + RPAR)

# Func. handles: http://www.mathworks.com/help/matlab/ref/function_handle.html

NAMED_FUNC_HANDLE  = '@' + ID_REF
ANON_FUNC_HANDLE   = '@' + LPAR + Group(Optional(ARG_LIST)) + RPAR + EXPR
FUNC_HANDLE        = Group(NAMED_FUNC_HANDLE | ANON_FUNC_HANDLE)

# Struct array references.  This is incomplete: in Matlab, the LHS can
# actually be a full expression that yields a struct.  Here, to avoid an
# infinitely recursive grammar, we only allow a specific set of objects and
# exclude a full EXPR.  (Doing the obvious thing, EXPR + "." + ID_REF, results
# in an infinitely-recursive grammar.)

STRUCT_BASE        = CELL_ARRAY_REF | MATRIX_REF | FUNCTION_CALL | FUNC_HANDLE | ID_REF
STRUCT_REF         = Group(STRUCT_BASE + "." + ID_REF)

# The transpose operator is a problem.  It seems you can actually apply it to
# full expressions, as long as the expressions yield an array.  Parsing the
# general case is hard because strings in Matlab use single quotes, so adding
# an operator that's a single quote confuses the parser.  The following
# approach is a hacky partial solution that only allows certain cases.

PARENTHESIZED_EXPR = LPAR + EXPR + RPAR
TRANSPOSABLES      = MATRIX_REF | ID_REF | BARE_MATRIX | PARENTHESIZED_EXPR
TRANSPOSE          = Group(TRANSPOSABLES.leaveWhitespace() + "'")

# The operator precendece rules in Matlab are listed here:
# http://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html

OPERAND            = Group(TRANSPOSE | FUNCTION_CALL | MATRIX_REF \
                           | CELL_ARRAY_REF | STRUCT_REF | FUNC_HANDLE \
                           | BARE_MATRIX | BARE_CELL_ARRAY \
                           | ID_REF | NUMBER | BOOLEAN | STRING)

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

ASSIGNED_ID        = (ID_BASE.copy()).setResultsName('vars', listAllMatches=True)
SIMPLE_ASSIGNMENT  = ASSIGNED_ID + EQUALS.suppress() + EXPR
OTHER_ASSIGNMENT   = (BARE_MATRIX | MATRIX_REF | CELL_ARRAY_REF | STRUCT_REF) + EQUALS.suppress() + EXPR
ASSIGNMENT         = OTHER_ASSIGNMENT | SIMPLE_ASSIGNMENT
ASSIGNMENT.addParseAction(store_assignment)

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
COMMAND_STMT_ARG   = Word(alphanums + "_")
COMMAND_STMT       = COMMON_COMMANDS | ID_REF + COMMAND_STMT_ARG

SINGLE_VALUE       = ID_REF
IDS_WITH_COMMAS    = delimitedList(SINGLE_VALUE)
IDS_WITH_SPACES    = OneOrMore(SINGLE_VALUE)
MULTIPLE_VALUES    = LBRACKET + (IDS_WITH_SPACES | IDS_WITH_COMMAS) + RBRACKET
FUNCTION_DEF_NAME  = ID_BASE.copy()
FUNCTION_LHS       = Optional(Group(MULTIPLE_VALUES | SINGLE_VALUE) + EQUALS)
FUNCTION_ARGS      = Optional(LPAR + ARG_LIST + RPAR)
FUNCTION           = Keyword('function').suppress()
FUNCTION_DEF_STMT  = Group(FUNCTION + FUNCTION_LHS + FUNCTION_DEF_NAME + FUNCTION_ARGS)

LINE_COMMENT       = Group('%' + restOfLine + EOL)
BLOCK_COMMENT      = Group('%{' + SkipTo('%}', include=True))
COMMENT            = (BLOCK_COMMENT | LINE_COMMENT).addParseAction(print_tokens)
DELIMITER          = COMMA | SEMI
CONTINUATION       = Combine(ELLIPSIS.leaveWhitespace() + EOL + EOS)
STMT               = Group(FUNCTION_DEF_STMT | CONTROL_STMT | ASSIGNMENT | COMMAND_STMT | EXPR).addParseAction(print_tokens)

MATLAB_SYNTAX      = ZeroOrMore(STMT | DELIMITER | COMMENT)
MATLAB_SYNTAX.ignore(CONTINUATION)

# This is supposed to be for optimization, but unless I call this, the parser
# simply never finishes parsing even simple inputs.
MATLAB_SYNTAX.enablePackrat()


# -----------------------------------------------------------------------------
# Interpretation of elements
# -----------------------------------------------------------------------------

BARE_MATRIX       .addParseAction(lambda x: tag_grammar(x, 'bare matrix'))
SINGLE_ROW        .addParseAction(lambda x: tag_grammar(x, 'single row'))
FUNCTION_CALL     .addParseAction(lambda x: tag_grammar(x, 'function call'))
FUNC_HANDLE       .addParseAction(lambda x: tag_grammar(x, 'function handle'))
SIMPLE_ASSIGNMENT .addParseAction(lambda x: tag_grammar(x, 'variable assignment'))
OTHER_ASSIGNMENT  .addParseAction(lambda x: tag_grammar(x, 'matrix/cell/struct assignment'))
FUNCTION_DEF_STMT .addParseAction(lambda x: tag_grammar(x, 'function definition'))
LINE_COMMENT      .addParseAction(lambda x: tag_grammar(x, 'comment'))
ID_REF            .addParseAction(lambda x: tag_grammar(x, 'id reference'))
EXPR              .addParseAction(lambda x: tag_grammar(x, 'expr'))


# -----------------------------------------------------------------------------
# Annotation of grammar for debugging.
#
# You can leave the setName(...) calls as-is.  To see debugging output, add a
# .setDebug(True) to an element.  Some examples are left commented out below.
# -----------------------------------------------------------------------------

ELLIPSIS          .setName('ELLIPSIS')
BOOLEAN           .setName('BOOLEAN')
STRING            .setName('STRING')
ID_REF            .setName('ID_REF')#.setDebug(True)
COMMENT           .setName('COMMENT')#.setDebug(True)
LINE_COMMENT      .setName('LINE_COMMENT')#.setDebug(True)
ARG_LIST          .setName('ARG_LIST')
ROWS              .setName('ROWS')#.setDebug(True)
BARE_MATRIX       .setName('BARE_MATRIX')#.setDebug(True)
MATRIX_REF        .setName('MATRIX_REF')
BARE_CELL_ARRAY   .setName('BARE_CELL_ARRAY')
CELL_ARRAY_REF    .setName('CELL_ARRAY_REF')
FUNCTION_CALL     .setName('FUNCTION_CALL')#.setDebug(True)
FUNC_HANDLE       .setName('FUNC_HANDLE')#.setDebug(True)
STRUCT_REF        .setName('STRUCT_REF')
TRANSPOSE         .setName('TRANSPOSE')
OPERAND           .setName('OPERAND')#.setDebug(True)
EXPR              .setName('EXPR')
COND_EXPR         .setName('COND_EXPR')
ASSIGNED_ID       .setName('ASSIGNED_ID')
ASSIGNMENT        .setName('ASSIGNMENT')#.setDebug(True)
CONTROL_STMT      .setName('CONTROL_STMT')
COMMON_COMMANDS   .setName('COMMON_COMMANDS')
COMMAND_STMT_ARG  .setName('CONTROL_STMT_ARG')
COMMAND_STMT      .setName('COMMAND_STMT')
FUNCTION_DEF_NAME .setName('FUNCTION_DEF_NAME')
FUNCTION_DEF_STMT .setName('FUNCTION_DEF_STMT')
SINGLE_VALUE      .setName('SINGLE_VALUE')
WHILE_STMT        .setName('WHILE_STMT')
IF_STMT           .setName('IF_STMT')
ELSEIF_STMT       .setName('ELSEIF_STMT')
ELSE_STMT         .setName('ELSE_STMT')
RETURN_STMT       .setName('RETURN_STMT')
BREAK_STMT        .setName('BREAK_STMT')
CONTINUE_STMT     .setName('CONTINUE_STMT')
GLOBAL_STMT       .setName('GLOBAL_STMT')
PERSISTENT_STMT   .setName('PERSISTENT_STMT')
FOR_ID            .setName('FOR_ID')
FOR_STMT          .setName('FOR_STMT')
SWITCH_STMT       .setName('SWITCH_STMT')
CASE_STMT         .setName('CASE_STMT')
OTHERWISE_STMT    .setName('OTHERWISE_STMT')
TRY_STMT          .setName('TRY_STMT')
CATCH_STMT        .setName('CATCH_STMT')
END               .setName('END')
FUNCTION          .setName('FUNCTION')
STMT              .setName('STMT')

# -----------------------------------------------------------------------------
# Direct run interface
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    debug = False
    if sys.argv[1] == '-d':
        debug = True
        path = sys.argv[2]
    else:
        path = sys.argv[1]

    file = open(path, 'r')
    print "----- file " + path + "-"*30
    contents = file.read()
    print contents
    print "----- output " + "-"*65
    result = parse_string(contents)
    if debug: pdb.set_trace()
    print "----- data dumps " + "-"*65
    # print result.asDict()
    # print result.pprint()
    # print_variables(result)
    # print_called(result)

