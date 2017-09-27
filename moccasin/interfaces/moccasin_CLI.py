#!/usr/bin/env python
#
# @file    moccasin.py
# @brief   Command-line interface for Moccasin
# @author  Harold Gomez
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
import plac
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from controller import Controller

# This prevents exceeding recursion depth in some cases.
sys.setrecursionlimit(1500)

# -----------------------------------------------------------------------------
# Main function - driver
# -----------------------------------------------------------------------------

def main(path, omit_comments=False, debug=False, use_equations=False,
         output_XPP=False, use_params=False, quiet=False, print_parse=False):
    '''A minimal interface for converting simple MATLAB models to SBML.'''
    #Flag-Option-Required-Default(FORD) convention was followed for function args declaration.
    #Flag arguments are first, then option arguments and required arguments, and finally default arguments.

    if not path.endswith('.m'):
        print('File "{}" does not appear to be a MATLAB file.'.format(path))
        sys.exit(1)

    add_comments = not omit_comments
    try:
        #Interface with the back-end
        controller = Controller()

        with open(path) as file:
            file_contents = file.read()
            if not quiet:
                print_header('File ' + path)
                print(file_contents)

            if debug:
                pdb.set_trace()

            controller.parse_File(file_contents)

            if print_parse and not quiet:
                print_header('Parsed MATLAB output')
                print(controller.print_parsed_results())

            if output_XPP:
                print_header('XPP output', quiet)
                output = controller.build_model(use_species=(not use_params),
                                                output_format="xpp",
                                                name_after_param=False,
                                                add_comments=add_comments)
                print(output)
            elif use_equations:
                print_header('Equation-based SBML output', quiet)
                output = controller.build_model(use_species=(not use_params),
                                                output_format="sbml",
                                                name_after_param=False,
                                                add_comments=add_comments)
                print(output)
            else:
                print_header('Reaction-based SBML output', quiet)
                if not controller.check_network_connection() and not quiet:
                    print('Error: a network connection is needed for this feature.')
                    sys.exit(1)

                sbml = controller.build_reaction_model(use_species=(not use_params),
                                                       name_after_param=False,
                                                       add_comments=add_comments)
                print(sbml)

    except Exception as err:
        print("Error: {0}".format(err))


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def print_header(text, quiet=False):
    if not quiet:
        print('')
        print('{:-^78}'.format(' ' + text + ' '))
        print('')

# -----------------------------------------------------------------------------
# Plac annotations for main function arguments
# -----------------------------------------------------------------------------

# Argument annotation follows (help, kind, abbrev, type, choices, metavar) convention
main.__annotations__ = dict(
    path          = ('path to MATLAB input file'),
    omit_comments = ('omit MOCCASIN version info in comments (default: include)',    'flag', 'c'),
    debug         = ('drop into pdb before parsing the MATLAB input',                'flag', 'd'),
    use_equations = ('create equation-based SBML (default: reaction-based SBML)',    'flag', 'e'),
    output_XPP    = ('create XPP ODE format instead of SBML format output',          'flag', 'o'),
    use_params    = ('encode variables as SBML parameters instead of SBML species',  'flag', 'p'),
    quiet         = ('be quiet: produce SBML and nothing else',                      'flag', 'q'),
    print_parse   = ('print extra debugging info about the interpreted MATLAB code', 'flag', 'x'),
)

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def cli_main():
    #The argument parser is inferred - it also deals with too few or too many func args
    plac.call(main)

cli_main()
