The purpose of this experiment is to try to use PLY 3.3 with OMPC and try to fix the "unknown conflict" error in OMPC's grammar.

I tried to hack the grammar in ompc/ompcply.py.

I was unable to get past a conflict in the parser grammar when using PLY 3.3.  Here's the output:

> python2.6 ompc/ompcply.py mfiles/add.m 
WARNING: Token 'COMMENT' defined, but not used
WARNING: There is 1 unused token
Generating LALR tables
Traceback (most recent call last):
  File "ompc/ompcply.py", line 822, in <module>
    yacc.yacc(debug=True)
  File "/Users/mhucka/projects/sysbio/sbml/software/moccasin/src/experiments/ompc-experiments/experiment-02/ompc/yacc.py", line 3220, in yacc
    lr = LRGeneratedTable(grammar,method,debuglog)
  File "/Users/mhucka/projects/sysbio/sbml/software/moccasin/src/experiments/ompc-experiments/experiment-02/ompc/yacc.py", line 1973, in __init__
    self.lr_parse_table()
  File "/Users/mhucka/projects/sysbio/sbml/software/moccasin/src/experiments/ompc-experiments/experiment-02/ompc/yacc.py", line 2450, in lr_parse_table
    raise LALRError("Unknown conflict in state %d" % st)
yacc.LALRError: Unknown conflict in state 26

