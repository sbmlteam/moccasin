'''__main__: Command line interface for MOCCASIN

This module implements a command-line interface to MOCCASIN.  It allows users
to invoke MOCCASIN from shell command lines.

Copyright
---------

This software is part of MOCCASIN, the Model ODE Converter for Creating
Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.

Copyright (C) 2014-2018 jointly by the following organizations:
    1. California Institute of Technology, Pasadena, CA, USA
    2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
    3. Boston University, Boston, MA, USA

This is free software; you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free
Software Foundation.  A copy of the license agreement is provided in the
file named "COPYING.txt" included with this software distribution and also
available online at https://github.com/sbmlteam/moccasin/.
'''

# Allow this program to be executed directly from the 'bin' directory.
import os
import sys
import plac

from .interfaces import moccasin_CLI

if __name__ == "__main__":
    plac.call(moccasin_CLI.cli_main)
