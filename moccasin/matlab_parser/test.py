#!/usr/bin/env python
#
# @file    test.py
# @brief   Simple test driver for MatlabGrammar class.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2015 jointly by the following organizations:
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
import sys
import getopt
from grammar import *


def get_filename_and_options(argv):
    try:
        options, path = getopt.getopt(argv[1:], "dpq")
    except:
        raise SystemExit(main.__doc__)
    if len(path) != 1 or len(options) > 2:
        raise SystemExit(main.__doc__)
    debug = any(['-d' in y for y in options])
    do_print = any(['-p' in y for y in options])
    quiet = any(['-q' in y for y in options])
    return path[0], debug, do_print, quiet


def main(argv):
    '''Usage: matlab_parser.py [-p] [-d] [-q] FILENAME.m
Arguments:
  -q   (Optional) Be quiet -- just print the output
  -p   (Optional) Print a representation of the output in the "old" format
  -d   (Optional) Drop into pdb as the final step
'''

    path, debug, print_old_format, quiet = get_filename_and_options(argv)

    file = open(path, 'r')
    if not quiet: print('----- file ' + path + ' ' + '-'*30)
    contents = file.read()
    if not quiet: print(contents)

    parser  = MatlabGrammar()
    results = parser.parse_string(contents)
    if not print_old_format:
        if not quiet: print('----- raw parse results ' + '-'*50)
        parser.print_parse_results(results, print_raw=True)
    else:
        if not quiet:
            print('----- raw parse results ' + '-'*50)
            parser.print_parse_results(results, print_raw=True)
        if not quiet: print('----- old format ' + '-'*50)
        parser.print_parse_results(results)

    if debug:
        print('-'*60)
        print('Debug reminder: parsed results are in variable `results`')
        print('-'*60)
        pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)