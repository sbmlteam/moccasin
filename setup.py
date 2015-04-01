#!/usr/bin/env python
#
# @file    setup.py
# @brief   Standard Python setup.py for MOCCASIN.
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
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from pkg_resources import require, DistributionNotFound
from codecs import open
from os import path
import re
import sys
import moccasin
from moccasin import __version__

here = path.abspath(path.dirname(__file__))

# If libSBML is not installed, notify user and exit installer
try:
    import libsbml
    pass

except(DistributionNotFound):
    print('')
    print('You do not have libsbml installed')
    print('Please refer to our quickstart file for instructions on downloading this module')
    sys.exit()

with open(path.join(here, 'requirements.txt')) as f:
    reqs = f.read().rstrip().encode("utf-8").splitlines()

class PyTest(TestCommand):
    # user_options = [('pytest-args=', 'vv', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='moccasin',
    version=__version__,
    url='https://github.com/sbmlteam/moccasin/',
    license='GNU Lesser General Public License',
    author='Michael Hucka, Sarah Keating, and Harold Gomez',
    tests_require=['pytest'],
    install_requires=reqs,
    cmdclass={'test': PyTest},
    author_email='email@sbml.com',
    description='MOCCASIN: the Model ODE Converter for Creating Awesome SBML INteroperability, a user-assisted converter that can take MATLAB or Octave ODE-based models in biology and translate them into the SBML format.',
    packages=find_packages(exclude='tests'),
    package_data={'moccasin': ['docs/*.md','LICENSE.txt', 'requirements.txt']},
    include_package_data=True,
    platforms='any',
    test_suite='tests',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License',
        'Operating System :: OS Independent'
        ],
         entry_points={
        'console_scripts': [
            'moccasin = moccasin.interfaces.moccasin_CLI:cli_main',
        ],
        'gui_scripts': [
            'moccasin-GUI = moccasin.interfaces.moccasin_GUI',
        ]
        }
)
