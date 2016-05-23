#!/usr/bin/env python
#
# @file    errors.py
# @brief   MATLAB converter exceptions.
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

import sys
import six
sys.path.append('..')

# MOCCASIN converter errors
# .............................................................................

class MoccasinException(Exception):
    """Base class for MOCCASIN exceptions."""
    pass


class FileError(MoccasinException):
    """Class of errors involving file access."""
    pass


class MatlabParsingError(MoccasinException):
    """Class of errors involving parsing the MATLAB input."""
    pass


class NotConvertibleError(MoccasinException):
    """Class of errors involving the structure of the MATLAB input."""
    pass


class IncompleteInputError(MoccasinException):
    """Class of errors involving incomplete MATLAB inputs."""
    pass


class UnsupportedInputError(MoccasinException):
    """Class of errors for unsupported MATLAB constructs or model formats."""
    pass


class ConversionError(MoccasinException):
    """Class of errors for general failures of MOCCASIN's conversion approach."""
    pass
