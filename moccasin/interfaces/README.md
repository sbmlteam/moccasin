Interfaces
======================

## Command-line interface

MOCCASIN's command-line interface (CLI) was written using [plac](https://pypi.python.org/pypi/plac), which is a simple wrapper for argparse. `plac` hides most of its complexity by using a declarative interface, so the argument parser is inferred from the signature of the main function rather than written down imperatively&mdash;simplifying things.


### Usage

If you have installed MOCCASIN by following the installation instructions, you should be able to run the command-line interface by typing the command `moccasin` into a shell/terminal (or if that fails, `python -m moccasin`). If you have not install MOCCASIN, you should still be able to run the command-line interface directly from this directory by executing `python -m moccasin_CLI.py`.  For information on options and customizing a MOCCASIN run, use the command-line flag `-h`.


### Functionality

Aside from a required MATLAB file, MOCCASIN's CLI supports several flags useful in the parsing and conversion to SBML:

* `-h` Prints help message
* `-c` omit the MOCCASION version comments normally written into the output
* `-d` Drop into pdb before starting to parse the MATLAB input
* `-e` Returns model as equation-based SBML (default: reaction-based SBML)
* `-o` Returns model in XPP format (default: SBML format)
* `-p` Encode variables as SBML parameters instead of SBML species
* `-q` Be quiet: produce SBML and nothing else
* `-x` Print extra debugging information about the interpreted MATLAB code

The one-character abbreviation used here allows for GNU-style composition of flags (i.e., `-qpe` is an abbreviation of `-q -p -e`).


## Graphical-user interface

MOCCASIN's graphical-user interface (GUI) was written using [wxPython](http://www.wxpython.org/), which is a toolkit that wraps the popular wxWidgets cross platform GUI library (C++). This means that Moccasin's interface runs on multiple platforms without modification. Currently supported platforms are 32-bit Microsoft Windows, most Unix or unix-like systems, and Macintosh OS X.


### Usage

If you have installed MOCCASIN per the installation instructions, you should be able to run MOCCASIN's graphical-user interface by typing the command `moccasin-GUI` into a shell/terminal (or if that fails, `python -m moccasin-GUI`.  If you have not installed MOCCASIN, you should still be able to execute `python -m moccasin_GUI.py` to run the GUI interface directly.  (Please note that in this case, the name uses an underscore `_` character and not a hyphen!)
