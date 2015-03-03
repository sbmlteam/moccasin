Command-line interface
========

###Design
Moccasin's command-line interface (CLI) was written using [plac](https://pypi.python.org/pypi/plac), which is a simple wrapper for argparse. Plac hides most of its complexity by using a declarative interface, so the argument parser is inferred from the signature of the main function rather than written down imperatively - simplifying things.

###Functionality
Aside from a required MATLAB file, Moccasin's CLI supports several flags useful in the parsing and conversion to SBML. 

* -h Prints help message
* -d Drop into pdb before starting to parse the MATLAB input
* -q Be quiet: produce SBML and nothing else
* -x Print extra debugging information about the interpreted MATLAB code
* -s Encode variables as species (default: parameters)

One-character abbreviation for flags: in this way you can use the GNU-style composition of flags (i.e. -qsd is an abbreviation of -q -s -x).

###Usage of settings files
