Abstract
--------

**Summary**: A common application of MATLAB in biological research is to model phenomena using ordinary differential equations (ODE) and simulate them with MATLAB's built-in ODE solvers. However, sharing these models with non-MATLAB users and other software environments can be a problem. Community-standard formats such as SBML can serve as a neutral exchange format, but translating MATLAB ODE models into SBML is a challenging task  – especially for modelers who have legacy models that were never written with translation in mind. We developed MOCCASIN (*Model ODE Converter for Creating Awesome SBML INteroperability*) to help with this task. MOCCASIN is an open-source translator that can convert ODE-based MATLAB models of biochemical reaction networks into SBML.

**Availability and Implementation**: MOCCASIN is released under the terms of the LGPL 2.1 license (http://www.gnu.org/licenses/lgpl-2.1.html). Source code, binaries and test cases can be freely obtained from https://github.com/sbmlteam/moccasin.

**Supplementary Information**: More information regarding the general implementation of MOCCASIN can be found in the user guide at https://github.com/sbmlteam/moccasin/tree/master.

**Contact**: moccasin-dev@googlegroups.com


1. INTRODUCTION 
----------------

MATLAB is a general-purpose numerical computing environment whose powerful features and interactive programming facilities have attracted many researchers. It has been the substrate for countless computational models as well as software tools written in its object-oriented programming language. Despite MATLAB's popularity, there are reasons why MATLAB programs are not themselves a desirable format for exchanging, publishing or archiving computational models in biology. These reasons include the lack of biological semantics in MATLAB programs, which makes clear interpretation of programs as models of biological processes more difficult; the fact that MATLAB is proprietary and expensive, which makes it unsuitable as a universal format for open scientific exchange; and the fact that model details are often intertwined with program implementation details, which makes it difficult to determine which parts constitute the essence of a model.

SBML (the Systems Biology Markup Language) is an open format for representing and exchanging models across software tools in systems biology (Hucka et al., 2003). Born from the need to resolve incompatibilities between systems that use different formats to describe model components, SBML is neutral with respect to modeling framework and computational platform – which helps ensure portability across tools, and ensures that models as research products can persist regardless of changes to any particular software tool or operating system. Over 280 different software tools have adopted SBML as an exchange format. Unfortunately, translating models from MATLAB form to SBML is not straightforward. MATLAB toolboxes such as the Systems Biology Toolbox (Schmidt and Mats, 2006) and the SBML Toolbox (Keating et al., 2006) do offer some SBML capabilities; however, they have limited utility for translating legacy models, lack support for handling the latest SBML releases, and require researchers to use them from the start of their model development.

These issues led us to develop MOCCASIN (*Model ODE Converter for Creating Awesome SBML INteroperability*), a stand-alone tool that can take ODE models written in MATLAB and export them as SBML files. MOCCASIN is written in Python and does not require access to MATLAB. It parses MATLAB code directly, optionally infers the reactions implied by the system of ODEs defined in the MATLAB code, and then exports an equivalent SBML file. To achieve this, we drew on recent theoretical advances in the inference of biochemical reaction networks (Fages et al., 2015). The result allows for richer SBML that can also be used for qualitative analyses where knowledge of the reaction network behind a system of ODEs is required.


2. IMPLEMENTATION
-----------------

MOCCASIN features a modular architecture comprised of the following: (1) a module that parses MATLAB input files; (2) a module that extracts the ODE-based model and produces a model with explicit differential equations in either SBML form or XPP (Ermentrout, 2002) form; (3) a module that uses The Biochemical Abstract Machine (BIOCHAM; Fages et al., 2015) to infer the biochemical reactions implied by the ODEs, and then post-processes the result to produce an SBML version with biochemical reactions for kinetics; (4) a command line interface; and (5) a graphical user interface. MOCCASIN is flexible enough to allow Python developers to use as few or as many modules as they desire.

### 2.1 Parsing module 

MATLAB is difficult to parse fully (Doherty et al., 2011): the language is complex and idiosyncratic, and there is no published definition of the MATLAB syntax rules. We did not attempt to develop a complete parser for MATLAB; instead, we leveraged the fact that MOCCASIN's input is already expected to be syntactically valid MATLAB (because users are converting working MATLAB code), and thus MOCCASIN's parser can be simpler and make more assumptions. The parser creates an internal representation that is essentially an embellished Abstract Syntax Tree (AST). 

### 2.2 Converter module

The AST produced by the parser module is then processed to recognize specific constructs. The approach centers on finding a call to one of the MATLAB `ode*NN*` family of solvers (e.g., `ode45`, `ode15s`, etc.). Once this call is found, the converter module then searches the AST for the definitions of the arguments to the call; these are expected to be either a matrix or the handle of a function that returns a matrix. When it is a function (which must be found elsewhere in the same file), MOCCASIN also inspects the parsed function body. The rows of the matrix or the function's return values are assumed to define the ODEs defined by the user's model. MOCCASIN performs some translation of the equations and then generates either an SBML representation (using SBML "rate rules") or an XPP/XPPAUT (Ermentrout, 2002) representation. To generate SBML, MOCCASIN makes use of libSBML (Bornstein et al., 2008), an application programming interface (API) library for working with SBML; to generate the simpler XPP output, MOCCASIN has a direct implementation of the necessary translation code.

### 2.3 BIOCHAM module

Encoding a model's ODE equations in a one-to-one fashion using SBML's "rate equations" is sufficient to ensure simulation reproducibility, but the translated model is not ideal if the original system of ODEs actually represents a biochemical reaction network. Reconstructing this network captures the underlying model more productively and enables subsequent application of analyses that require biochemical reactions (e.g., Gay et al., 2014 Fages et al., 2004). In order to export SBML models with fully resolved reaction networks, MOCCASIN sends the output from the converter module to BIOCHAM’s web service via Simple Object Access Protocol (SOAP), and post-processes the result to produce SBML with reaction definitions. BIOCHAM is a modeling environment for systems biology that encompasses the published implementation of a state-of-the-art algorithm for reconstructing and inferring the complete reaction model from a given set of ODEs (Fages et al., 2015).

Due to XPP's syntactic limitations as well as limitations in BIOCHAM, the model retrieved from BIOCHAM lacks a variety of components present in the original model (including initial assignments, references to the time variable, units, and others). To accurately translate more of the ODE-based MATLAB model and accommodate a wider range of modeling scenarios, the output from BIOCHAM is post-processed to add initial assignments, references to the time variable (if used in the original model), and other missing pieces. All components of the initial MATLAB file are thus modeled and each reaction in the final SBML system is fully characterized with well-identified reactants, products and modifiers.

### 2.4 Command-line interface

MOCCASIN provides a cross-platform, user-friendly command-line interface (CLI) as well as a graphical-user interface (GUI). Command-line runs may be customized via flags which, for instance, allow the display of debugging information or enable the encoding of model variables as SBML "parameters" instead of SBML "species". 

### 2.5 Graphical user interface

MOCCASIN's GUI interface is implemented with a cross-platform GUI toolkit. The interface provides a straightforward way for users to input MATLAB files, set MOCCASIN options such as the type of output (SBML or XPP), view the resulting output, and save the converted file.


FUTURE WORK
-----------

MATLAB code supplied to MOCCASIN must conform to certain simple forms and make limited use of MATLAB functions and operators. Future enhancements will (1) expand the grammar that the parser understands, so that more MATLAB constructs can be interpreted; (2) support models spread over several MATLAB input files; (3) generate SED-ML (Simulation Experiment Description Markup Language; Waltemath et al., 2011) files, which encode procedural aspects that cannot be expressed in SBML; and (4) directly implement the BIOCHAM reaction inference algorithm (Fages et al., 2015), which will streamline the translation process, free MOCCASIN from the limitations of the XPP format, and avoid the need for post-processing BIOCHAM output.


ACKNOWLEDGEMENTS
----------------

The authors thank Thomas B. Kepler, Franz-Josef Elmer, Bernd Rinn and Jannik Vollmer for their helpful discussions and implementation ideas.

*Funding*: This work was supported by the Modeling Immunity for Biodefense contract by the National Institutes of Health (NIH contract numbers HHSN266200500021C, awarded to Stuart Sealfon; and HHSN272201000053C, awarded to Thomas B. Kepler and Garnett H. Kelsoe). We also acknowledge support by the Swiss Institute of Bioinformatics.

*Conflict of Interest*: none declared.


REFERENCES
----------

Bornstein, B.J. et al. (2008) LibSBML: an API Library for SBML. Bioinformatics, 24, 880-881.

Doherty, J., Hendren, L., & Radpour, S. (2011). Kind analysis for MATLAB. In Proceedings of OOPSLA'11. 

Ermentrout, B. (2002) Simulating, analyzing, and animating dynamical systems: a guide to XPPAUT for researchers and students. Society for Industrial Mathematics.

Fages, F. et al. (2004) Modelling and querying interaction networks in the biochemical abstract machine BIOCHAM. J. Biol. Phys. Chem., 4 (2): 64–73.

Fages, F. et al. (2015) Inferring Reaction Systems from Ordinary Differential Equations. Theoretical Computer Science, 22 (4): 514-515.

Gay, S. et al. (2014) On the Subgraph Epimorphism Problem. Discrete Applied Mathematics, 162: 214–228.

Hucka, M. et al. (2003) The systems biology markup language (SBML): a medium for representation and exchange of biochemical network models. Bioinformatics, 19, 524-531.

Keating, S.M. et al. (2006) SBMLToolbox: An SBML Toolbox for MATLAB Users. Bioinformatics, 22 (10): 1275–1277.

Schmidt, H., and Mats J. (2006) Systems Biology Toolbox for MATLAB: A Computational Platform for Research in Systems Biology. Bioinformatics, 22 (4): 514–515.

Waltemath, D., et al. (2011). Reproducible computational biology experiments with SED-ML -- the simulation experiment description markup language. BMC Systems Biology, 5 (1): 198.
