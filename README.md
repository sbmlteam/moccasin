MOCCASIN
========

*MOCCASIN* stands for *"Model ODE Converter for Creating Awesome SBML INteroperability"*.  It is a project to develop a user-assisted converter that can take MATLAB or Octave ODE-based models in biology and translate them into [SBML](http://sbml.org) format.

----
*Authors*:      Sarah Keating (http://www.ebi.ac.uk/about/people/sarah-keating) and
Michael Hucka (http://www.cds.caltech.edu/~mhucka) 

*Copyright*:    Copyright (C) 2014 by the California Institute of Technology, Pasadena, USA.

*License*:      This code is licensed under the LGPL version 2.1.  Please see the file [../COPYING.txt](https://raw.githubusercontent.com/sbmlteam/moccasin/master/COPYING.txt) for details.

*Repository*:   https://github.com/sbmlteam/moccasin


Background
----------

The Systems Biology Markup Language ([SBML](http://sbml.org)) is a machine-readable representation format for computational models of biological processes.  By supporting SBML as an input/output format, different tools can all operate on an identical representation of a model, removing opportunities for translation errors and assuring a common starting point for analyses and simulations.

As part of our continuing efforts to develop SBML and useful software tools around it, we previously created [SBMLToolbox](http://sbml.org/Software/SBMLToolbox).  It allows an SBML model to be imported into [MATLAB](http://www.mathworks.com) and [Octave](http://octave.org), where the model is represented as a data structure that users can manipulate using the facilites of those environments; likewise, the data structure can be exported to SBML form.  One of the features that SBMLToolbox does *not* provide, however, is the ability to convert free-form, unstructured MATLAB/Octave differential equation models into SBML: if the user did not write their MATLAB/Octave model using the SBMLToolbox data structure in the first place, then there is no way to export it in SBML form.  However, users have repeatedly asked us for a way to do this.

The goal of this project is to provide a solution to this by developing a new software package, MOCCASIN (*"Model ODE Converter for Creating Awesome SBML INteroperability"*). MOCCASIN will be a user-assisted converter that helps researchers take models written in MATLAB and Octave without SBMLToolbox or any other similar toolboxes, and export them as SBML files.  Although a fully automated and general converter will be impossible, it should be possible to translate at least *some* MATLAB/Octave models using a combination of heuristics and user assistance.  Doing so will enable researchers to exchange and publish their models in a standard format accepted by hundreds of journals and to take advantage of hundreds of software tools that support SBML today.


Versioning
----------

This project uses the [Semantic Versioning](http://semver.org) principles for versioning.  The version number has the format `MAJOR.MINOR.PATCH-LABEL`. The fields have the following meaning:

* An increment of the major version number, `MAJOR`, represents incompatible API changes.
* An increment of the minor version number, `MINOR`, represents additional functionality in a backwards-compatible manner.
* An increment of the patch version number, `PATCH`, represents backwards-compatible bug fixes.
* Existence of a label `LABEL` represents a pre-release or build metadata.


License
-------

Copyright (C) 2014 by the California Institute of Technology, Pasadena, USA.

This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or any later version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and documentation provided hereunder is on an "as is" basis, and the California Institute of Technology has no obligations to provide maintenance, support, updates, enhancements or modifications.  In no event shall the California Institute of Technology be liable to any party for direct, indirect, special, incidental or consequential damages, including lost profits, arising out of the use of this software and its documentation, even if the California Institute of Technology has been advised of the possibility of such damage.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this library in the file named "COPYING.txt" included with the software distribution.
