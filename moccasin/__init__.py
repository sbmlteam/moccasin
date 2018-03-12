#!/usr/bin/env python
#
# @file    __init__.py
# @brief   MOCCASIN package __init__ file
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2017 jointly by the following organizations:
#     1. California Institute of Technology, Pasadena, CA, USA
#     2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
#     3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

from .__version__ import __version__, __title__, __url__
from .__version__ import __author__, __author_email__
from .__version__ import __license__, __license_url__, __help_url__

from .matlab_parser import MatlabParser
from .interfaces import moccasin_CLI, moccasin_GUI
from .converter import create_raterule_model, process_biocham_output
