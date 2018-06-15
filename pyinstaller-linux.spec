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

# Code to find LibSBML native library
# .............................................................................

def libsbml_lib_name():
    py_version = str(sys.version_info.major) + str(sys.version_info.minor)
    if 'Ubuntu' in platform.dist():
        if '64bit' in platform.architecture():
            plat = '-x86_64-linux-gnu'
        else:
            plat = '-x86_32-linux-gnu'
    elif 'centos' in platform.dist():
        plat = ''
    return '_libsbml.cpython-' + py_version + 'm' + plat + '.so'

def libsbml_lib_path():
    return os.path.join(imp.find_module('libsbml')[1], libsbml_lib_name())


# Main PyInstaller definitions
# .............................................................................

if 'Ubuntu' in platform.dist():
    other_libs = [ ("libGL.so", "/usr/lib/x86_64-linux-gnu/libGL.so", 'BINARY') ]
elif 'centos' in platform.dist():
    other_libs = [ ("libGL.so", "/usr/lib64/libGL.so", 'BINARY') ]
else:
    other_libs = []

configuration = Analysis(['moccasin/__main__.py'],
                         pathex = ['.'],
                         binaries = [(libsbml_lib_path(), '.')],
                         datas = [],
                         hiddenimports = [],
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
                         configuration.binaries + other_libs,
                         configuration.zipfiles,
                         configuration.datas,
                         name = 'moccasin',
                         debug = False,
                         strip = False,
                         upx = True,
                         runtime_tmpdir = None,
                         console = False,
                        )

app             = BUNDLE(executable,
                         name = 'MOCCASIN.app',
                         icon = 'dev/icon/moccasin.ico',
                         bundle_identifier = None,
                         info_plist = {'NSHighResolutionCapable': 'True'},
                        )
