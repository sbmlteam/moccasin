#!/usr/bin/env python
#
# @file    run-evaluate-tests.py
# @brief   Test runner for MOCCASIN evaluation class.
# @author  Sarah Keating
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2017 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

from __future__ import print_function
import glob
import sys
import pdb
import getopt

sys.path.append('../../moccasin/converter/')
sys.path.append('../../moccasin/')

from evaluate_formula import *


def main(argv):
    """
    Usage: run-evaluate-tests.py [options]
    Available options:
      -n  (Optional) Don't drop into pdb upon a parsing exception -- keep going.
      -v  (Optional) Print intermediate debugging output.
   """

    try:
        options, path = getopt.getopt(argv[1:], "nv")
    except:
        raise SystemExit(main.__doc__)

    do_print = any(['-v' in y for y in options])
    do_debug = not any(['-n' in y for y in options])

    for f in glob.glob("evaluate-test-cases/valid_*.m"):
        print('===== ' + f + ' ' + '='*30)
        with open(f, 'r') as file_in:
            contents = file_in.read()
        print(contents.rstrip())

        if do_print:
            print('----- output ' + '-'*30)
        results = ''
        try:
            formula_parser = NumericStringParser()
            formula = contents
            if formula is not None and formula != '':
                results = formula_parser.eval(formula)

            print(results)

        except Exception as err:
            print('threw exception')
            print(err)
            if do_debug and not results:
                print('Object "results" contains the output of eval()')
                pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)
