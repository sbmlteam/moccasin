#
# @file    Makefile
# @brief   Makefile for some steps in creating a MOCCASIN application
# @author  Michael Hucka
# @date    2018-06-09
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

# Variables.

release    := $(shell egrep 'version.*=' moccasin/__version__.py | awk '{print $$3}' | tr -d "'")
platform   := $(shell python -c 'import sys; print(sys.platform)')
macos_vers := $(shell sw_vers -productVersion 2>/dev/null | cut -f1-2 -d'.' || true)
github-css := dev/github-css/github-markdown-css.html

# Main build targets.

build: build-$(platform)

# Platform-specific instructions.

build-darwin: dist/MOCCASIN.app ABOUT.html NEWS.html
	packagesbuild dev/installer-builders/macos/packages-config/MOCCASIN.pkgproj
	mv dist/MOCCASIN-mac.pkg dist/MOCCASIN-$(release)-macos-$(macos_vers).pkg 

dist/MOCCASIN.app dist/MOCCASIN.exe: clean
	pyinstaller pyinstaller-$(platform).spec

# Component files placed in the installers.

ABOUT.html: README.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o README.html README.md
	inliner -n < README.html > ABOUT.html

NEWS.html: NEWS.md
	pandoc --standalone --quiet -f gfm -H $(github-css) -o NEWS.html NEWS.md
	inliner -n < NEWS.html > NEWS-inlined.html
	mv NEWS-inlined.html NEWS.html

# Miscellaneous directives.

clean:;
	-rm -fr dist build ABOUT.html NEWS.html

.PHONY: html clean
