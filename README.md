MOCCASIN
========

*MOCCASIN* stands for *"Model ODE Converter for Creating Awesome SBML INteroperability"*.  It is a project to develop a user-assisted converter that can take MATLAB or Octave ODE-based models in biology and translate them into [SBML](http://sbml.org) format.

----
*Authors*:      [Michael Hucka](http://www.cds.caltech.edu/~mhucka), [Sarah Keating](http://www.ebi.ac.uk/about/people/sarah-keating), and [Harold G&oacute;mez](http://www.bu.edu/computationalimmunology/people/harold-gomez/).

*Copyright*:    Copyright (C) 2014-2015 jointly by the California Institute of Technology (Pasadena, California, USA) and the Mount Sinai School of Medicine (New York, New York, USA).

*License*:      This code is licensed under the LGPL version 2.1.  Please see the file [../COPYING.txt](https://raw.githubusercontent.com/sbmlteam/moccasin/master/COPYING.txt) for details.

*Repository*:   [https://github.com/sbmlteam/moccasin](https://github.com/sbmlteam/moccasin)

*Developers' discussion group*: [https://groups.google.com/forum/#!forum/moccasin-dev](https://groups.google.com/forum/#!forum/moccasin-dev)

*Pivotal tracker*: [https://www.pivotaltracker.com/n/projects/977060](https://www.pivotaltracker.com/n/projects/977060)


Background
----------

Computation modeling has become a crucial aspect of biological research, and [SBML](http://sbml.org) (the Systems Biology Markup Language) has become the de facto standard open format for exchanging models between software tools in systems biology. [MATLAB](http://www.mathworks.com) and [Octave](http://www.gnu.org/software/octave/) are popular numerical computing environments used by modelers in biology, but while toolboxes for using SBML exist, many researchers either have legacy models or do not learn about the toolboxes before starting their work and then find it discouragingly difficult to export their MATLAB/Octave models to SBML.

The goal of this project is to develop software that uses a combination of heuristics and user assistance to help researchers export models written as ordinary MATLAB and Octave scripts. MOCCASIN  (*"Model ODE Converter for Creating Awesome SBML INteroperability"*) will help researchers take models written in MATLAB and Octave without SBMLToolbox or any other similar toolboxes, and export them as SBML files.  Although a fully automated and general converter will be probably be impossible, it should be possible to translate at least *some* MATLAB/Octave models using a combination of heuristics and user assistance.  Doing so will enable researchers to exchange and publish their models in a standard format accepted by hundreds of journals and to take advantage of hundreds of software tools that support SBML today.

Funding
-------

This work is made possible thanks to funding from the Mount Sinai School of Medicine in New York City, provided as part of the NIH-funded project *Modeling Immunity for Biodefense* (Principal Investigator: [http://www.mountsinai.org/profiles/stuart-c-sealfon](Stuart Sealfon)).


License
-------

Copyright (C) 2014-2015 jointly by the California Institute of Technology (Pasadena, California, USA) and the Mount Sinai School of Medicine (New York, New York, USA).

This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or any later version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and documentation provided hereunder is on an "as is" basis, and the California Institute of Technology has no obligations to provide maintenance, support, updates, enhancements or modifications.  In no event shall the California Institute of Technology be liable to any party for direct, indirect, special, incidental or consequential damages, including lost profits, arising out of the use of this software and its documentation, even if the California Institute of Technology has been advised of the possibility of such damage.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this library in the file named "COPYING.txt" included with the software distribution.
