Command-line interface
========
Moccasin's command-line interface (CLI) was written using [plac](https://pypi.python.org/pypi/plac), which is a simple wrapper for argparse. Plac hides most of its complexity by using a declarative interface, so the argument parser is inferred from the signature of the main function rather than written down imperatively - simplifying things.

###Usage
To run Moccasin's command-line script installation, simply open the command line and type ```moccasin.py filename```. For info on adding options and customizing a Moccasin run, use ```moccasin.py -h```.

###Functionality
Aside from a required MATLAB file, Moccasin's CLI supports several flags useful in the parsing and conversion to SBML. 

* -h Prints help message
* -d Drop into pdb before starting to parse the MATLAB input
* -q Be quiet: produce SBML and nothing else
* -x Print extra debugging information about the interpreted MATLAB code
* -p Encode variables as parameters (default: species)
* -e Returns model as equation-based SBML (default: reaction-based SBML)
* -o Returns model in XPP format (default: SBML format)

The one-character abbreviation used here allows for GNU-style composition of flags (i.e. -qpe is an abbreviation of -q -p -e).


