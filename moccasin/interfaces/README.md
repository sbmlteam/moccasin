Interfaces
======================

##Command-line interface

MOCCASIN's command-line interface (CLI) was written using [plac](https://pypi.python.org/pypi/plac), which is a simple wrapper for argparse. `plac` hides most of its complexity by using a declarative interface, so the argument parser is inferred from the signature of the main function rather than written down imperatively&mdash;simplifying things.

### Usage

To run MOCCASIN's command-line interface, simply type the command `moccasin FILENAME` into a shell/terminal, where *FILENAME* is the path to the MATLAB file to be converted. For info on adding options and customizing a MOCCASIN run, use `moccasin -h`.

### Functionality

Aside from a required MATLAB file, MOCCASIN's CLI supports several flags useful in the parsing and conversion to SBML:

* `-h` Prints help message
* `-d` Drop into pdb before starting to parse the MATLAB input
* `-q` Be quiet: produce SBML and nothing else
* `-x` Print extra debugging information about the interpreted MATLAB code
* `-p` Encode variables as SBML parameters instead of SBML species
* `-e` Returns model as equation-based SBML (default: reaction-based SBML)
* `-o` Returns model in XPP format (default: SBML format)

The one-character abbreviation used here allows for GNU-style composition of flags (i.e., `-qpe` is an abbreviation of `-q -p -e`).


##Graphical-user interface
MOCCASIN's graphical-user interface (GUI) was written using [wxPython](http://www.wxpython.org/), which is a toolkit that wraps the popular wxWidgets cross platform GUI library (C++). This means that Moccasin's interface runs on multiple platforms without modification. Currently supported platforms are 32-bit Microsoft Windows, most Unix or unix-like systems, and Macintosh OS X.

### Usage

To run MOCCASIN's graphical-user interface, simply type the command `moccasin-GUI` into a shell/terminal.
