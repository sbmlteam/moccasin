#!/usr/bin/env python
#
# @file    run-syntax-tests.py
# @brief   Test runner for MOCCASIN MATLAB parser.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

import glob
import sys
import pdb
import getopt
from pyparsing import ParseException, ParseResults
sys.path.append('..')
from matlab import *

parser = MatlabGrammar()


def main(argv):
    '''Usage: run-syntax-tests.py [-d] [-v]
    Arguments:
      -n  (Optional) Don't drop into pdb upon a parsing exception -- keep going.
      -v  (Optional) Print intermediate debugging output.
    '''

    try:
        options, path = getopt.getopt(argv[1:], "nv")
    except:
        raise SystemExit(main.__doc__)

    do_debug = not any(['-n' in y for y in options])
    do_print = any(['-v' in y for y in options])

    for f in glob.glob("syntax-test-cases/valid*.m"):
        print('===== ' + f + ' ' + '='*30)
        with open(f, 'r') as file:
            contents = file.read()
        print(contents.rstrip())
        if do_print:
            print('----- output ' + '-'*30)
        try:
            results = parser.parse_string(contents, print_debug=do_print, fail_soft=True)
        except Exception as err:
            if do_debug and not results:
                print('Object "results" contains the output of parse_string()')
                pdb.set_trace()
        print('----- interpreted ' + '-'*30)
        parser.print_parse_results(results)
        print('')


if __name__ == '__main__':
    main(sys.argv)
