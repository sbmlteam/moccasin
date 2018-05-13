#!/usr/bin/env python
#
# @file    singleton.py
# @brief   Singleton metaclass
# @author  Michael Hucka
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

# This implements the Singleton metaclass from Chapter 9 of the book "Python
# Cookbook" 3rd edition by David Beazly & Brian K. Jones (O'Reilly, 2013),
# modified to work in Python 2 following an example in StackOverflow here:
# http://stackoverflow.com/a/6798042/743730

class Singleton(type):
    """Singleton metaclass.  Usage example:

    class Spam(metaclass=Singleton):
        def __init__(self):
            print('foo')
    """

    def __init__(self, *args, **kwargs):
        self.__instance = None
        super(Singleton, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(Singleton, self).__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance
