#!/usr/bin/env python
#
# @file    test.py
# @brief   Simple test driver for MatlabGrammar class.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
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

# Basic principles
# ----------------
#
# This is a simple test driver for the parser module.  You can invoke it
# on the command line as follows:
#
#    ./test.py matlabfile.m
#
# where "matlabfile.m" is some (preferrably very simple) matlab input file.
# test.py will parse the file using MatlabGrammar.parse_string() and print an
# annotated representation of how the input was interpreted.  This
# representation is in the form of a MatlabContext object for the input file
# "matlabfile.m".  If given the optional argument -d, then test.py invokes
# the Python pdb debugger after parsing the input, thus allowing you to
# inspect the resulting data structure interactively.  The parse results are
# stored in the compellingly-named variable "results".  To begin debugging,
# you could print the values of the fields in the MatlabContext object, such
# as "nodes", "types", "assignments", "functions", "calls", and others.

from __future__ import print_function
import sys
import getopt
from grammar import *

def get_filename_and_options(argv):
    '''Helper function for parsing command-line arguments.'''
    try:
        options, path = getopt.getopt(argv[1:], "dpqi")
    except:
        raise SystemExit(main.__doc__)
    if len(path) != 1 or len(options) > 2:
        raise SystemExit(main.__doc__)
    print_debug = any(['-d' in y for y in options])
    print_old = any(['-p' in y for y in options])
    quiet = any(['-q' in y for y in options])
    interactive_pdb = any(['-i' in y for y in options])
    return path[0], print_debug, print_old, quiet, interactive_pdb


def main(argv):
    '''Usage: matlab_parser.py [-d] [-i] [-p] [-q] FILENAME.m
Arguments:
  -d   (Optional) Print extremely detailed debug output during parsing
  -i   (Optional) Drop into pdb as the final step
  -p   (Optional) Print a representation of the output in the "old" format
  -q   (Optional) Be quiet -- just print the output
'''

    path, debug, print_old, quiet, interactive = get_filename_and_options(argv)

    with open(path, 'r') as file:
        if not quiet: print('----- file ' + path + ' ' + '-'*30)
        contents = file.read()
        if not quiet: print(contents)
        file.close()

    with MatlabGrammar() as parser:
        # This uses parse_string() instead of parse_file() because the file has
        # already been opened.  This is a minor performance improvement in case
        # someone tries to read a really huge file -- no sense reading it twice.
        results = parser.parse_string(contents, print_debug=debug)
        # parse_string() doesn't set the name of the file in the context object,
        # so let's do it ourselves as a convenience to the user.
        results.file = path
        if not print_old:
            if not quiet: print('----- raw parse results ' + '-'*50)
            parser.print_parse_results(results, print_raw=True)
        else:
            if not quiet:
                print('----- raw parse results ' + '-'*50)
                parser.print_parse_results(results, print_raw=True)
            if not quiet: print('----- old format ' + '-'*50)
            parser.print_parse_results(results)

        if interactive:
            print('-'*60)
            print('Debug reminder: parsed results are in variable `results`')
            print('-'*60)
            pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)
