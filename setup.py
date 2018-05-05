#!/usr/bin/env python3
#
# @file    setup.py
# @brief   Standard Python setup.py for MOCCASIN.
# @author  Harold Gomez
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

from __future__ import print_function
from setuptools import setup, find_packages, Extension
from setuptools.command.test import test as TestCommand
from pkg_resources import require, DistributionNotFound
from codecs import open
import os
from os import path
import re
import sys
from sys import platform

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'requirements.txt')) as f:
    reqs = f.read().rstrip().splitlines()

class PyTest(TestCommand):
    user_options = [('test-suite=', 't', "Tests to run")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Import here, because outside the eggs aren't loaded.
        import pytest
        # I couldn't get the documented example to work, so here's my version
        # of passing arguments.
        if sys.argv[-1].startswith('tests'):
            errno = pytest.main(sys.argv[-1])
        else:
            errno = pytest.main(self.pytest_args)
        sys.exit(errno)

# The following reads the variables without doing an "import moccasin",
# because the latter will cause the python execution environment to fail if
# any dependencies are not already installed -- negating most of the reason
# we're using setup() in the first place.  This code avoids eval, for security.

version = {}
with open(path.join(here, 'moccasin/__version__.py')) as f:
    text = f.read().rstrip().splitlines()
    vars = [line for line in text if line.startswith('__') and '=' in line]
    for v in vars:
        setting = v.split('=')
        version[setting[0].strip()] = setting[1].strip().replace("'", '')

# Installing python-libsbml involves compiling libsbml, and gcc may generate
# warnings.  The warnings are benign and not something that users of Moccasin
# can do anything about anyway.  The next line silences the warnings.

if platform.startswith('linux'):
    os.environ['CFLAGS'] = '-Wno-strict-prototypes -Wno-switch -Wno-maybe-uninitialized'
else:
    os.environ['CFLAGS'] = '-Wno-enum-conversion -Wno-strict-prototypes -Wno-switch'

# Finally, define our namesake.

setup(
    name                 = version['__title__'].lower(),
    version              = version['__version__'],
    url                  = version['__url__'],
    author               = version['__author__'],
    author_email         = version['__email__'],
    license              = version['__license__'],
    description          = version['__description__'],
    keywords             = "biology simulation file-conversion differential-equations MATLAB SBML",
    install_requires     = reqs,
    tests_require        = ['pytest', 'pytest-xdist'],
    test_suite           = 'tests',
    cmdclass             = {'test': PyTest},
    packages             = find_packages(exclude = 'tests'),
    package_data         = {'moccasin': ['../README.md', '../LICENSE.txt',
                                         '../docs/quickstart.md']},
    include_package_data = True,
    platforms            = 'any',
    python_requires      = '>=3',
    scripts              = ['bin/moccasin'],
    classifiers          = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License',
        'Operating System :: OS Independent'
    ],
)
