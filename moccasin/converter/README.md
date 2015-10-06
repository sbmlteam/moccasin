MOCCASIN converter module
=========================

This subdirectory contains the converter that produces [SBML](http://sbml.org) and other output from the parsed MATLAB input.

The AST produced by the MOCCASIN parser module (in `../matlab_parser`) is processed to recognize specific constructs.  The approach centers on finding a call to one of the MATLAB `ode*NN*` family of solvers (e.g., `ode45`, `ode15s`, etc.).  Once this call is found, the converter module then searches the AST for the definitions of the arguments to the call; these are expected to be either a matrix or the handle of a function that returns a matrix.  When it is a function (which must be found elsewhere in the same file), MOCCASIN also inspects the parsed function body.  The rows of the matrix or the function's return values are assumed to define the ODEs defined by the user's model.  MOCCASIN performs some translation of the equations, and generates either an SBML representation (using SBML *rate rules*) or an [XPP/XPPAUT](http://www.math.pitt.edu/~bard/xpp/xpp.html) representation.  To generate SBML, MOCCASIN makes use of [libSBML](http://sbml.org/Software/libSBML), an application programming interface (API) library for working with SBML; to generate the simpler XPP output, MOCCASIN has a direct implementation of the necessary translation code.  Exported SBML files retain the model semantics of the MATLAB ODE model, and use SBML *rate equations* to describe their temporal evolution.