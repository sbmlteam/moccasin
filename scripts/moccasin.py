#!/usr/bin/env python
#
# @file    CLI.py
# @brief   Command-line interface for Moccasin
# @author  Harold Gomez
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.

from __future__ import print_function
from pyparsing import ParseException, ParseResults
from tempfile import NamedTemporaryFile
import plac
import sys
import requests
sys.path.append('moccasin/converter/')
sys.path.append('moccasin/')
from matlab_parser import *
from converter import *

# -----------------------------------------------------------------------------
# Main function - driver
# -----------------------------------------------------------------------------

def main(debug, quiet, print_parse, use_params, use_equations, output_XPP, filename):
    "A minimal interface for MATLAB file parsing and conversion to SBML"
    #Flag-Option-Required-Default(FORD) convention was followed for function args declaration.
    #Flag arguments are first, then option arguments and required arguments, and finally default arguments.
    if filename.endswith('.m'):  
        file = open(filename, 'r')
        file_contents = file.read()
        file.close()
      
        if not quiet:
            yield('----- file ' + filename + ' ' + '-'*30)
            yield(file_contents)

        if debug:
            pdb.set_trace()
                
        try:
            parser = MatlabGrammar()
            parse_results = parser.parse_string(file_contents)
        except ParseException as err:
            yield("error: {0}".format(err))

        if print_parse and not quiet:
            yield('')
            yield('----- interpreted output ' + '-'*50)
            parser.print_parse_results(parse_results)

        if output_XPP:
            yield('')
            yield('----- XPP output ' + '-'*50)
            output= create_raterule_model(parse_results, not use_params, not output_XPP)
            yield(output)

        else:  
            if use_equations:
                yield('')
                yield('----- Equation-based SBML output ' + '-'*50)
                output= create_raterule_model(parse_results, not use_params, not output_XPP)
                yield(output)
            else:
                yield('')
                yield('----- Reaction-based SBML output ' + '-'*50)
                #Create temp file storing XPP model version
                try:
                    with NamedTemporaryFile(suffix= ".ode", delete=False) as xpp_file:
                        xpp_file.write(create_raterule_model(parse_results, not use_params, output_XPP))
                    files = {'file':open(xpp_file.name)}                
                    #Access Biocham to curate and convert equations to reactions
                    url = 'http://lifeware.inria.fr/biocham/online/rest/export'
                    data = {'exportTo':'sbml', 'curate':'true'}
                    response = requests.post(url, files=files, data=data)
                    del files
                    yield(response.content)
                except IOError as err:
                    yield("error: {0}".format(err))
                finally:            
                 os.unlink(xpp_file.name)
    else:
        yield("usage: filename used must be a MATLAB file")
        
# -----------------------------------------------------------------------------
# Plac annotations for main function arguments
# -----------------------------------------------------------------------------
      
#Argument annotation follows (help, kind, abbrev, type, choices, metavar) convention
main.__annotations__ = dict(
    debug=('Drop into pdb before starting to parse the MATLAB input', 'flag', 'd'),
    quiet=('Be quiet: produce SBML and nothing else', 'flag', 'q'),
    print_parse=('Print extra debugging information about the interpreted MATLAB code', 'flag', 'x'),
    use_params=('Encode variables as parameters (default: species)', 'flag', 'p'),
    use_equations=('Returns model as equation-based SBML (default: reaction-based SBML)', 'flag', 'e'),
    output_XPP=('Returns model in XPP format (default: SBML format)', 'flag', 'o'),
    filename=('path of MATLAB file'))

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
   
if __name__ == '__main__':
    #The argument parser is inferred - it also deals with too few or too many func args
    for output in plac.call(main):
        print(output)


#Export files (equation-based SBML / .ODE / reaction-based SBML)
