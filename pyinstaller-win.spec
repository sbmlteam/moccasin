# -*- mode: python -*-
#
# @file    pyinstaller-macos.spec
# @brief   Spec file for PyInstaller for macOS
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2018 jointly by the following organizations:
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

import imp
import os
import platform
import sys

# Main PyInstaller definitions
# .............................................................................

configuration = Analysis([r'moccasin\__main__.py'],
                         pathex = ['.'],
                         binaries = [],
                         datas = [(r'dev\icon\moccasin.ico', 'img')],
                         hiddenimports = ['libsbml._libsbml'],
                         hookspath = [],
                         runtime_hooks = [],
                         excludes = [],
                         win_no_prefer_redirects = False,
                         win_private_assemblies = False,
                         cipher = None,
                        )

application_pyz    = PYZ(configuration.pure,
                         configuration.zipped_data,
                         cipher = None,
                        )

executable         = EXE(application_pyz,
                         configuration.scripts,
                         configuration.binaries,
                         configuration.zipfiles,
                         configuration.datas,
                         name = 'moccasin',
                         icon = r'dev\icon\moccasin.ico',
                         # The extra manifest contents I added seem to be
                         # ignored. Leaving this here anyway, in case I want
                         # to file a bug report or patch pyinstaller.
                         manifest = r'dev/installer-builders/windows/moccasin.exe.manifest',
                         debug = False,
                         strip = False,
                         upx = False,
                         runtime_tmpdir = None,
                         console = False,
                        )

app             = BUNDLE(executable,
                         name = 'MOCCASIN.exe',
                         icon = r'dev\icon\moccasin.ico',
                         bundle_identifier = None,
                         info_plist = {'NSHighResolutionCapable': 'True'},
                        )
