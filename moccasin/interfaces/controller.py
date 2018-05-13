#!/usr/bin/env python
#
# @file    moccasin.py
# @brief   Controller that interfaces Moccasin's back-end with CLI and GUI
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
from pyparsing import ParseException, ParseResults
from tempfile import NamedTemporaryFile
import os
import sys
import requests
import pdb

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import moccasin
from moccasin.converter import create_raterule_model, process_biocham_output
from moccasin.converter import sanity_check_matlab
from moccasin.matlab_parser import MatlabParser
from moccasin.errors import UnsupportedInputError

# -----------------------------------------------------------------------------
# Global configuration constants
# -----------------------------------------------------------------------------

_BIOCHAM_URL = 'http://lifeware.inria.fr/biocham/online/rest/export'

# -----------------------------------------------------------------------------
# Controller class definition
# -----------------------------------------------------------------------------

class Controller():
    '''This class serves to interface between the CLI and GUI.'''

    def __init__(self):
        self.parser = MatlabParser()
        self.file_contents = None
        self.parse_results = None


    def parse_file(self , file_contents):
        '''Parses input file using Moccasin's parser.'''
        self.file_contents = file_contents
        self.parse_results = self.parser.parse_string(self.file_contents)


    def check_translatable(self, relaxed = False):
        '''Check the parsed MATLAB and complain if we can't translate it.'''
        try:
            sanity_check_matlab(self.parse_results)
            return True
        except Exception as e:
            if relaxed and isinstance(e,  moccasin.UnsupportedInputError):
                return True
            raise
        return False


    def print_parsed_results(self):
        '''Prints the parsed input file.'''
        return (self.parser.print_parse_results(self.parse_results, print_raw=True))


    def build_model(self, use_species, output_format, name_after_param, add_comments):
        '''Converts a parsed file into XPP or equation-based SBML.'''
        (output, _, _) = create_raterule_model(self.parse_results, use_species,
                                               output_format, name_after_param,
                                               add_comments)
        return output


    def build_reaction_model(self, use_species, name_after_param, add_comments):
        '''Converts a parsed file into reaction-based SBML.'''
        try:
            # Create temp file storing XPP model version
            with NamedTemporaryFile(suffix=".ode", delete=False) as xpp_file:
                (output, add, convert) = create_raterule_model(self.parse_results,
                                                               use_species,
                                                               "biocham",
                                                               name_after_param,
                                                               add_comments)

                # Python 3 changed the way temporary files read/wrote data
                # and used bytes that need to encoded/decoded.
                try:
                    xpp_file.write(output)
                except:
                    xpp_file.write(output.encode('UTF-8'))
                xpp_file.flush()
                xpp_file.close()
                files = {'file': open(xpp_file.name)}
            # Access BIOCHAM to curate and convert equations to reactions.
            data = {'exportTo':'sbml', 'curate':'true'}
            response = requests.post(_BIOCHAM_URL, files=files, data=data)
            del files

            # We need to post-process the output to deal with
            # limitations in BIOCHAM's translation service.
            sbml = process_biocham_output(response.content, self.parse_results,
                                          post_add=add, post_convert=convert,
                                          add_comments=add_comments)
            return(sbml)
        except IOError as err:
            print("error: {0}".format(err))
        finally:
            os.unlink(xpp_file.name)
