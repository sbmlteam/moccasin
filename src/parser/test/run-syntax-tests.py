#!/usr/bin/env python

import glob
import sys
from pyparsing import ParseException, ParseResults
sys.path.append('../matlab')
from grammar import *

for path in glob.glob("syntax-test-cases/valid*.m"):
    file = open(path, 'r')
    print '----- file ' + path + ' ' + '-'*30
    contents = file.read()
    print contents.rstrip()

    print '----- output ' + '-'*30
    try:
        parser  = MatlabGrammar()
        results = parser.parse_string(contents, False)
    except ParseException as err:
        print("error: {0}".format(err))
    file.close()
    print results
