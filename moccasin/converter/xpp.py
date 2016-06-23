#!/usr/bin/env python
#
# @file    xpp.py
# @brief   Classes to store pieces of the XPP output we produce.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2016 jointly by the following organizations:
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

class XPPDocument():
    def __init__(self, xpp_subset="biocham"):
        # Whether we're generating straight XPP or XPP-for-BIOCHAM output.
        self.xpp_subset = xpp_subset
        # In the internal storage format we use until we generate XPP output,
        # the components are stored in the following list.  It's a list
        # rather than a dictionary because we need to keep the elements in
        # order.  (The MATLAB might have assignments that depend on prior
        # assignments, which doesn't matter in SBML but does matter in XPP
        # when using XPP's name=formula "fixed" variables.)  Each element on
        # this list will be an XPPVar() object.
        self.vars = []
        # This will be a list of tuples:
        self.post_convert = []
        # This will be a list of tuples:
        self.post_add = []


class XPPVar():
    def __init__(self, type=None, id='', constant=False, init_value=None,
                 init_assign=None, assign_rule=None, rate_rule=None):
        self.type        = type
        self.id          = id
        self.constant    = constant
        self.init_value  = init_value
        self.init_assign = init_assign
        self.assign_rule = assign_rule
        self.rate_rule   = rate_rule
