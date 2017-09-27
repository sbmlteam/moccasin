#!/usr/bin/env python
#
# @file    name_generator.py
# @brief   Generate names with a counter.
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

import sys
import six
sys.path.append('..')
try:
    from .singleton import Singleton
except:
    from singleton import Singleton


@six.add_metaclass(Singleton)
class NameGenerator(object):
    """Generates a name consisting of a prefix string followed by an integer.

    Each invocation of the method `name()` will increment the counter used for
    the value of the number.  The prefix string defaults to "name", but can be
    set to something else by using the keyword argument prefix="string" when
    calling the method name().

    This class is implemented as a singleton.  All instances of this class in a
    running copy of a Python program using this class will share the same
    counter.
    """

    def __init__(self):
        self._counter = 0


    def name(self, prefix='name'):
        """Returns a unique name consisting of a prefix string and an integer.
        The default prefix string is "name".  The keyword argument "prefix"
        can be used to set a different prefix string.  The number is always
        unique for a given instance of this class, regardless of the prefix.
        """
        self._counter += 1
        return '{}{:03d}'.format(prefix, self._counter)


    def reset(self):
        self._counter = 0
