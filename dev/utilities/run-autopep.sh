#!/bin/sh
#
# @file    run-autopep.sh
# @brief   Script to run autopep8 with a specific configuration
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#     1. California Institute of Technology, Pasadena, CA, USA
#     2. Mount Sinai School of Medicine, New York, NY, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

# For the meanings of these codes, see the following:
# http://pep8.readthedocs.org/en/latest/intro.html#error-codes

IGNORE=E226,E221,E227,E241,E501,E126

autopep8 -a --ignore $IGNORE $*
