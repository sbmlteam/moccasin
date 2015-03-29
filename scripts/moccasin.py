#!/usr/bin/env python
#
# @file    moccasin.py
# @brief   Command-line interface for Moccasin
# @author  Harold Gomez
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2015 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

from __future__ import print_function
from pyparsing import ParseException, ParseResults
from tempfile import NamedTemporaryFile
import plac
import sys
import os
import requests
sys.path.append('moccasin/')
sys.path.append('../moccasin/')
sys.path.append('moccasin/converter/')
sys.path.append('../moccasin/converter/')
from version import __version__
from matlab_parser import *
from converter import *

# This prevents exceeding recursion depth in some cases.
sys.setrecursionlimit(1500)

# -----------------------------------------------------------------------------
# Global configuration constants
# -----------------------------------------------------------------------------

_BIOCHAM_URL = 'http://lifeware.inria.fr/biocham/online/rest/export'

# -----------------------------------------------------------------------------
# Main function - driver
# -----------------------------------------------------------------------------

def main(path, debug=False, quiet=False, use_equations=False, use_params=False,
         output_XPP=False, print_parse=False):
    '''A minimal interface for converting simple MATLAB models to SBML.'''
    #Flag-Option-Required-Default(FORD) convention was followed for function args declaration.
    #Flag arguments are first, then option arguments and required arguments, and finally default arguments.

    if not path.endswith('.m'):
        print('File "{}" does not appear to be a MATLAB file.'.format(path))
        sys.exit(1)

    try:
        with open(path) as file:
            file_contents = file.read()
            if not quiet:
                print_header('File ' + path)
                print(file_contents)

            if debug:
                pdb.set_trace()

            parser = MatlabGrammar()
            parse_results = parser.parse_string(file_contents)

            if print_parse and not quiet:
                print_header('Parsed MATLAB output')
                parser.print_parse_results(parse_results)

            if output_XPP:
                print_header('XPP output', quiet)
                [output, extra] = create_raterule_model(parse_results,
                                                        use_species=(not use_params),
                                                        produce_sbml=(not output_XPP),
                                                        use_func_param_for_var_name=True)
                print(output)
            elif use_equations:
                print_header('Equation-based SBML output', quiet)
                [output, extra] = create_raterule_model(parse_results,
                                                        use_species=(not use_params),
                                                        produce_sbml=(not output_XPP),
                                                        use_func_param_for_var_name=True)
                print(output)
            else:
                print_header('Reaction-based SBML output', quiet)
                if not network_available() and not quiet:
                    print('Error: a network connection is needed for this feature.')
                    sys.exit(1)
                try:
                    # Create temp file storing XPP model version
                    with NamedTemporaryFile(suffix=".ode", delete=False) as xpp_file:
                        [xpp_output, extra] = create_raterule_model(parse_results,
                                                                    use_species=(not use_params),
                                                                    produce_sbml=False,
                                                                    use_func_param_for_var_name=True)
                        xpp_file.write(xpp_output)
                    files = {'file': open(xpp_file.name)}
                    # Access Biocham to curate and convert equations to reactions
                    data = {'exportTo':'sbml', 'curate':'true'}
                    response = requests.post(_BIOCHAM_URL, files=files, data=data)
                    del files
                    # We need to post-process the output to deal with
                    # limitations in BIOCHAM's translation service.
                    sbml = process_biocham_output(response.content,
                                                  parse_results, extra)
                    yield(sbml)
                except IOError as err:
                    yield("error: {0}".format(err))
                finally:
                    os.unlink(xpp_file.name)

    except Exception as err:
        yield("Error: {0}".format(err))


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def print_header(text, quiet=False):
    if not quiet:
        print('')
        print('{:-^78}'.format(' ' + text + ' '))
        print('')


def network_available():
    '''Try to connect somewhere to test if a network is available.'''
    try:
        _ = requests.get('http://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False


# -----------------------------------------------------------------------------
# Plac annotations for main function arguments
# -----------------------------------------------------------------------------

# Argument annotation follows (help, kind, abbrev, type, choices, metavar) convention
main.__annotations__ = dict(
    path          = ('path to MATLAB input file'),
    debug         = ('drop into pdb before parsing the MATLAB input',                'flag', 'd'),
    quiet         = ('be quiet: produce SBML and nothing else',                      'flag', 'q'),
    print_parse   = ('print extra debugging info about the interpreted MATLAB code', 'flag', 'x'),
    use_params    = ('encode variables as SBML parameters instead of SBML species',  'flag', 'p'),
    use_equations = ('create equation-based SBML (default: reaction-based SBML)',    'flag', 'e'),
    output_XPP    = ('create XPP ODE format instead of SBML format output',          'flag', 'o')
)

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ ==  '__main__':
    #The argument parser is inferred - it also deals with too few or too many func args
    for output in plac.call(main):
        print(output)


#Export files (equation-based SBML / .ODE / reaction-based SBML)
