Abstract
========

**Summary**: MATLAB is a general-purpose numerical computing environment that is widely used in the life sciences.  A common application in biological research is to model processes using ordinary differential equations (ODE) and simulate them with MATLAB's built-in ODE solvers.  While working in MATLAB is undeniably convenient, sharing the resulting models with non-MATLAB users and other software environments can be a problem.  Community-standard formats such as SBML can serve as a neutral exchange format, but translating MATLAB ODE models into such a format is a challenging task, especially for modelers who have legacy models that were never written with translation to SBML in mind.  To help with this task, we developed MOCCASIN (*Model ODE Converter for Creating Awesome SBML INteroperability*), an open-source converter that uses a combination of heuristics and user assistance.  MOCCASIN offers a straightforward solution for converting MATLAB-based models in which ODEs represent systems of biochemical reactions, into an equivalent SBML model.

**Availability and Implementation**: MOCCASIN is released under the terms of the LGPL 2.1 license (http://www.gnu.org/licenses/lgpl-2.1.html). Source code, binaries and test cases can be freely obtained from https://github.com/sbmlteam/moccasin.

**Supplementary Information**: More information regarding the general implementation of MOCCASIN can be found in the user guide at https://github.com/sbmlteam/moccasin/tree/master.

**Contact**: moccasin-dev@googlegroups.com


1. INTRODUCTION 
================

MATLAB is a popular numerical computing environment whose powerful features and interactive programming facilities have attracted many researchers.  It has been the substrate for countless computational models as well as software tools written in its object-oriented programming language.  Nevertheless, there are reasons why MATLAB programs are not, in and of themselves, a desirable format for exchanging, publishing or archiving computational models in biology.  These include the lack of biological semantics in MATLAB programs, which makes interpretation of programs as models of biological processes more difficult; the fact that MATLAB itself is proprietary and expensive, which makes it unsuitable as a universal format for worldwide scientific exchange; and the fact that in programs and scripts, model details are often intertwined with implementation details, which makes it difficult for anyone but the authors to understand precisely which parts constitute the essence of a model.

SBML (the Systems Biology Markup Language) is a widely-accepted open format for representing and exchanging models across analysis and simulation tools in systems biology (Hucka et al., 2003). Born from the need to resolve incompatibilities between software platforms that use different formats to describe model components, SBML is neutral with respect to modeling framework and computational platform – which helps ensure portability and integration across tools, and ensures that models as research products can persist regardless of changes to any particular software tool or operating system. This has led to over 280 different software tools adopting SBML as a file format for model encoding.  Translating models from MATLAB form to SBML, however, has not been straightforward.  Popular MATLAB toolboxes such as the Systems Biology Toolbox (Schmidt and Mats, 2006) and the SBML Toolbox (Keating et al., 2006) offer a degree of indirect SBML manipulation from within MATLAB, but are limited: they lack support for handling the latest SBML releases, they require researchers to know about and use the toolboxes right from the beginning of their modeling work, and they are of limited use for translating legacy models.

These issues led us to develop MOCCASIN (*Model ODE Converter for Creating Awesome SBML INteroperability*), a stand-alone tool that helps researchers take ODE models written in MATLAB and Octave, and export them as SBML files. MOCCASIN is written in Python and does not require access to MATLAB.  It parses MATLAB code directly, optionally infers the reactions implied by the system of ODEs defined in the code, and then exports an equivalent SBML file.  To achieve this, we drew on recent theoretical advances in the inference of biochemical reaction networks (Fages et al., 2015). The result allows for richer SBML that can also be used for qualitative analyses where knowledge of the reaction network behind a system of ODEs is needed.  MOCCASIN is not intended to provide the ability to directly or indirectly manipulate MATLAB or SBML code; rather, MOCCASIN serves as a translator that delivers SBML code with the same model elements and kinetics as a given ODE MATLAB file.


2. IMPLEMENTATION
=================

MOCCASIN features a modular architecture comprised of the following: (1) a module that parses MATLAB input files into an internal parse tree representation; (2) a module that processes the representation to extract the ODE-based model and produce a model with explicit differential equations in either SBML form or in XPP form (Ermentrout, 2002); (3) a module that uses The Biochemical Abstract Machine (BIOCHAM; Fages et al., 2015) to infer the biochemical reactions implied by the ODEs and then post-processes the result to produce an SBML version with biochemical reactions for kinetics; (4) a command line interface; and (5) a graphical user interface.  MOCCASIN is flexible enough to allow Python developers to use as few or as many modules as they desire.

2.1 Parsing module 
------------------

MATLAB is notoriously difficult to parse (Doherty et al., 2011): the language is complex and idiosyncratic, there is no complete definition of the MATLAB syntax rules, and changes are sometimes introduced in new MATLAB releases.  We did not attempt to develop a complete parser for MATLAB; instead, we leveraged the fact that MOCCASIN's input is already expected to be syntactically valid MATLAB (because users are converting running MATLAB code), and thus MOCCASIN's parser can be simpler and make more assumptions.  The parser is implemented in part using PyParsing (McGuire, 2007), a Python parser library, and creates an internal representation that is essentially an embellished Abstract Syntax Tree (AST).  The current MOCCASIN parser implements a weak form of kind analysis (Doherty et al., 2011) to infer whether a given construct of the form `name(arguments)` is a function call or a references to a matrix (which are syntactically identical in the MATLAB language).  This area is one where MOCCASIN can be improved in future work.

2.2 Converter module
--------------------

The AST produced by the parser module is processed by the converter to recognize specific constructs.  The procedure centers on finding a call to one of the MATLAB `ode*NN*` family of solvers (e.g., `ode45`, `ode15s`, etc.).  Once this call is found, the converter then searches the AST for the definitions of the arguments to the call; these are expected to be either a matrix or the handle of a function that returns a matrix.  In the case of a function, which is expected to be found elsewhere in the same file, MOCCASIN also inspects the parsed function body.  The rows of the matrix or the function's return values are assumed to constitute the ODEs defined by the user's model.  MOCCASIN performs some translation of the equations, and generates either an SBML representation (using SBML "rate rules") or an XPP/XPPAUT (Ermentrout, 2002) representation.  To generate SBML, MOCCASIN makes use of libSBML (Bornstein et al., 2008), an application programming interface (API) library for working with SBML; to generate the simpler XPP output, MOCCASIN has a direct implementation of the necessary translation code.  (The XPP output is used by the BIOCHAM module discussed below.)  Exported SBML files retain the intended model semantics of the initial MATLAB ODE model, and use SBML rate equations to describe their temporal evolution.

2.3 BIOCHAM module
------------------

Although encoding the ODE equations of a model in a one-to-one fashion using SBML's "rate equations" is sufficient to ensure simulation reproducibility, the resulting model is not ideal if the original system of ODEs actually represents a biochemical reaction network.  Reconstructing the reaction network would capture the underlying model more productively and enable subsequent application of analyses that work from reaction networks, such as methods reason about the structure of reaction networks.  Among others, these include approaches to reduce models using graph theory concepts (Gay et al., 2014) and reachability assessments in reaction networks (Fages et al., 2004).

In order to export SBML models with fully resolved reaction networks, the MOCCASIN BIOCHAM module sends the output from the converter module to BIOCHAM’s web service, and post-processes the result to produce SBML with reaction definitions. BIOCHAM is a modeling environment for systems biology that encompasses the published implementation of a state-of-the-art algorithm for reconstructing and inferring the complete reaction model from a given set of ODEs (Fages et al., 2015). Pipeline interaction with BIOCHAM is done via a Simple Object Access Protocol (SOAP) call, which enables the supply of parsed input in the form of an XPP file and the retrieval of output in SBML form.

Due to syntactic limitations in XPP as well as limitations in BIOCHAM, the model retrieved from BIOCHAM lacks a variety of components present in the original model (including initial assignments, references to the time variable, units, and others).  In order to accurately translate the entire input ODE-based MATLAB model and accommodate as wide a range of modeling scenarios as possible, the output from BIOCHAM is post-processed to add initial assignments, references to the time variable (if used in the original model), and other missing pieces.  In this way, all components of the initial MATLAB file are modeled and each reaction in the final SBML system is fully characterized with well-identified reactants, products and modifiers.

2.4 Command-line interface
--------------------------

MOCCASIN provides a cross-platform, user-friendly command-line interface (CLI) as well as a graphical-user interface (GUI). Command-line runs may be customized via flags which, for instance, allow the display of debugging information or enable the encoding of model variables as SBML "parameters" instead of SBML "species". 

2.5 Graphical user interface
----------------------------

MOCCASIN's GUI interface is implemented using wxPython, a cross-platform GUI toolkit (Rappin and Dunn, 2006).  The interface provides a straightforward way for users to input MATLAB files, set MOCCASIN options such as the type of output (SBML or XPP), view the resulting output, and saving the converted file.


FUTURE WORK
===========

The current implementation of MOCCASIN works for MATLAB inputs that conform to certain simple forms and make limited use of MATLAB.  Future enhancements will focus on the following: (1) expand the grammar that the parser understands to enable the interpretation and processing of more MATLAB constructs, such as flow control; (2) support models spread over several MATLAB input files; (3) generate SED-ML (Simulation Experiment Description Markup Language) files, to encode procedural aspects that are cannot be expressed in SBML; and (4) implement the BIOCHAM reaction inference algorithm (Fages et al., 2015) directly, rather than relying on the web service.  The last will streamline the translation system, free MOCCASIN from the limitations of the XPP format, and avoid the need for post-processing the output of BIOCHAM.


ACKNOWLEDGEMENTS
================

The authors would like to acknowledge Thomas B. Kepler, Franz-Josef Elmer, Bernd Rinn and Jannik Vollmer for their helpful discussions and implementation ideas.

*Funding*: This work was supported by the Modeling Immunity for Biodefense contract by the National Institutes of Health (NIH contract numbers HHSN266200500021C, awarded to Stuart Sealfon; and HHSN272201000053C, awarded to Thomas B. Kepler and Garnett H. Kelsoe). We also acknowledge support by the Swiss Institute of Bioinformatics.

*Conflict of Interest*: none declared.


REFERENCES
==========

Bornstein, B.J. et al. (2008) LibSBML: an API Library for SBML. Bioinformatics, 24, 880-881.

Doherty, J., Hendren, L., & Radpour, S. (2011). Kind analysis for MATLAB. In Proceedings of OOPSLA'11. 

Ermentrout, B. (2002) Simulating, analyzing, and animating dynamical systems: a guide to XPPAUT for researchers and students. Society for Industrial Mathematics.

Fages, F. et al. (2004) Modelling and querying interaction networks in the biochemical abstract machine BIOCHAM. J. Biol. Phys. Chem., 4 (2): 64–73.

Fages, F. et al. (2015) Inferring Reaction Systems from Ordinary Differential Equations. Theoretical Computer Science, 22 (4): 514-515.

Gay, S. et al. (2014) On the Subgraph Epimorphism Problem. Discrete Applied Mathematics, 162: 214–228.

Ghosh, S. et al. (2011) Software for Systems Biology: From Tools to Integrated Platforms. Nature Reviews Genetics, 12: 821-832.

Hucka, M. et al. (2003) The systems biology markup language (SBML): a medium for representation and exchange of biochemical network models. Bioinformatics, 19, 524-531.

Keating, S.M. et al. (2006) SBMLToolbox: An SBML Toolbox for MATLAB Users. Bioinformatics, 22 (10): 1275–1277.

McGuire, P. (2007). Getting started with pyparsing. O'Reilly Media, Inc.

Rappin, N., & Dunn, R. (2006). WxPython in action. Manning Publications Co.

Schmidt, H., and Mats J. (2006) Systems Biology Toolbox for MATLAB: A Computational Platform for Research in Systems Biology. Bioinformatics, 22 (4): 514–515.
