MOCCASIN modules
----------------

MOCCASIN features a modular architecture comprised of the following: (1) a module that parses MATLAB input files; (2) a module that extracts the ODE-based model and produces a model with explicit differential equations in either SBML form or XPP/XPPAUT form; (3) a module that uses The Biochemical Abstract Machine (BIOCHAM) to infer the biochemical reactions implied by the ODEs and then post-processes the result to produce an SBML version with biochemical reactions for kinetics; (4) a command line interface; and (5) a graphical user interface.

The following is a summary of the subdirectories of this directory that contain the various modules and interfaces comprising MOCCASIN.

### matlab_parser

This subdirectory contains the MATLAB parser implementation.  MATLAB is difficult to parse fully: the language is complex and idiosyncratic, and there is no complete definition of the MATLAB syntax rules.  We did not attempt to develop a complete parser for MATLAB; instead, we leveraged the fact that MOCCASIN's input is already expected to be syntactically valid MATLAB (because users are converting working MATLAB code), and thus MOCCASIN's parser can be simpler and make more assumptions.  The parser is creates an internal representation that is essentially an embellished Abstract Syntax Tree (AST).  The current MOCCASIN parser implements a weak form of kind analysis ([Doherty et al., 2011](http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.295.5052)) to infer whether a given construct of the form `name(arguments)` is a function call or a references to a matrix (which are syntactically identical in the MATLAB language).

### converter

This subdirectory contains the converter that produces [SBML](http://sbml.org) and other output.  The AST produced by the parser module described above is processed to recognize specific constructs.  The approach centers on finding a call to one of the MATLAB `ode*NN*` family of solvers (e.g., `ode45`, `ode15s`, etc.).  Once this call is found, the converter module then searches the AST for the definitions of the arguments to the call; these are expected to be either a matrix or the handle of a function that returns a matrix.  When it is a function (which must be found elsewhere in the same file), MOCCASIN also inspects the parsed function body.  The rows of the matrix or the function's return values are assumed to define the ODEs defined by the user's model.  MOCCASIN performs some translation of the equations, and generates either an SBML representation (using SBML *rate rules*) or an [XPP/XPPAUT](http://www.math.pitt.edu/~bard/xpp/xpp.html) representation.  To generate SBML, MOCCASIN makes use of [libSBML](http://sbml.org/Software/libSBML), an application programming interface (API) library for working with SBML; to generate the simpler XPP output, MOCCASIN has a direct implementation of the necessary translation code.  Exported SBML files retain the model semantics of the MATLAB ODE model, and use SBML *rate equations* to describe their temporal evolution.

### interfaces

This subdirectory contains different interfaces for MOCCASIN, modularized to make MOCCASIN flexible enough so that Python developers can use as few or as many modules as they desire.

MOCCASIN provides a cross-platform, user-friendly command-line interface (CLI) as well as a graphical-user interface (GUI). Command-line runs may be customized via flags which, for instance, allow the display of debugging information or enable the encoding of model variables as SBML *parameters* instead of SBML *species*. 

MOCCASIN also provides a graphical user interface.  The GUI is implemented using [wxPython](http://wxpython.org), a cross-platform GUI toolkit.  The interface provides a straightforward way for users to input MATLAB files, set MOCCASIN options such as the type of output (SBML or XPP), view the resulting output, and saving the converted file.
