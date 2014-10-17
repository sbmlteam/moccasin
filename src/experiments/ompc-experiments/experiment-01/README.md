This is an experiment to get the OMPC Matlab-to-Python translator running as-is.  The subdiretories "ompc", "ompclib" and "mfiles" contain copies of the subdirectories of the same name from the OMPC 1.0-beta distribution.  This needs Python 2.6 to run (because that's what OMPC states it needs).

Code modifications:
- ompc/yacc.py: changed to use hashlib instead of deprecated md5 library
- ompc/ompcply.py: commented out p_expression_option(p)


The following example command will run with some yacc warnings:

  python2.6 ompc/ompcply.py mfiles/add.m

Result:

yacc: Warning. Token 'COMMENT' defined, but not used.
yacc: Warning. There is 1 unused token.
yacc: Generating LALR parsing table...
Unknown conflict in state 25
yacc: 562 shift/reduce conflicts
yacc: 217 reduce/reduce conflicts
@mfunction("out")
def add(a=None, b=None):
    # adds values of a and b
    out = a + b

