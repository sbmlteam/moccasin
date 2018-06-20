MOCCASIN
========

<img align="right" src="https://raw.githubusercontent.com/sbmlteam/moccasin/master/docs/project/logo/moccasin_logo_20151002/logo_128.png"> *MOCCASIN* stands for *"Model ODE Converter for Creating Automated SBML INteroperability"*.  MOCCASIN is designed to convert certain basic forms of ODE simulation models written in MATLAB or Octave and translate them into [SBML](http://sbml.org) format.  It thereby enables researchers to convert MATLAB models into an open and widely-used format in systems biology.

[![License](http://img.shields.io/:license-LGPL-blue.svg)](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html)  [![Latest version](https://img.shields.io/badge/Latest_version-1.3.0-brightgreen.svg)](http://shields.io) [![DOI](http://img.shields.io/badge/DOI-10.22002%20%2F%20D1.965-blue.svg)](https://data.caltech.edu/records/965)
[![Build Status](https://travis-ci.org/sbmlteam/moccasin.svg?branch=master)](https://travis-ci.org/sbmlteam/moccasin) [![Coverage Status](https://coveralls.io/repos/sbmlteam/moccasin/badge.svg?branch=master)](https://coveralls.io/r/sbmlteam/moccasin?branch=master)

*Authors*:      [Michael Hucka](http://www.cds.caltech.edu/~mhucka), [Sarah Keating](http://www.ebi.ac.uk/about/people/sarah-keating), and [Harold G&oacute;mez](http://www.bu.edu/computationalimmunology/people/harold-gomez/).<br>
*License*:      This code is licensed under the LGPL version 2.1.  Please see the file [../LICENSE.txt](https://raw.githubusercontent.com/sbmlteam/moccasin/master/LICENSE.txt) for details.<br>
*Code repository*:   [https://github.com/sbmlteam/moccasin](https://github.com/sbmlteam/moccasin)<br>
*Developers' discussion group*: [https://groups.google.com/forum/#!forum/moccasin-dev](https://groups.google.com/forum/#!forum/moccasin-dev)


🏁 Recent news and activities
------------------------------

_June 2018_: With version 1.3.0, we now distribute MOCCASIN as a self-contained program&mdash;users do not even need to install Python to run MOCCASIN.  In addition, the previous release 1.2.0 included a fix for a critical performance bug, with the consequence that MOCCASIN should run an order of magnitude faster than the last release.  Additional changes include several important bug fixes, improvements to the installation instructions, a change to keyboard shortcuts, and improved diagnostics in the GUI interface.  Please see the [NEWS.md](NEWS.md) file for more details.


Table of Contents
-----------------

* [Please cite the MOCCASIN paper and the version you use](#️-please-cite-the-moccasin-paper-and-the-version-you-use)
* [Background and introduction](#-background-and-introduction)
* [How it works](#-how-it-works)
* [Installation and configuration](#-installation-and-configuration)
* [Using MOCCASIN](#-using-moccasin)
* [Getting help and support](#-getting-help-and-support)
* [Do you like it?](#-do-you-like-it)
* [Contributing — info for developers](#-contributing--info-for-developers)
* [Acknowledgments](#-acknowledgments)
* [Copyright and license](#-copyright-and-license)


♥️ Please cite the MOCCASIN paper and the version you use
---------------------------------------------------------

Article citations are **critical** for us to be able to continue support for MOCCASIN.  If you use MOCCASIN and you publish papers about work that uses MOCCASIN, we ask that you **please cite the MOCCASIN paper**:

<dl>
<dd>
Harold F. Gómez, Michael Hucka, Sarah M. Keating, German Nudelman, Dagmar Iber and Stuart C. Sealfon.  <a href="http://bioinformatics.oxfordjournals.org/content/32/12/1905">MOCCASIN: converting MATLAB ODE models to SBML</a>. <i>Bioinformatics</i> (2016), 32(12): 1905-1906.
</dd>
</dl>

Please also use the DOI to indicate the specific version you use, to improve other people's ability to reproduce your results:

* MOCCASIN release 1.3.0 &rArr; [10.22002/D1.965](https://doi.org/10.22002/D1.965)
* MOCCASIN release 1.2.0 &rArr; [10.22002/D1.940](https://doi.org/10.22002/D1.940)
* MOCCASIN release 1.1.2 &rArr; 
[10.5281/zenodo.883135](https://doi.org/10.5281/zenodo.883135)


☀ Background and introduction
-----------------------------

Computational modeling has become a crucial aspect of biological research, and [SBML](http://sbml.org) (the Systems Biology Markup Language) has become the de facto standard open format for exchanging models between software tools in systems biology. [MATLAB](http://www.mathworks.com) and [Octave](http://www.gnu.org/software/octave/) are popular numerical computing environments used by modelers in biology, but while toolboxes for using SBML exist, many researchers either have legacy models or do not learn about the toolboxes before starting their work and then find it discouragingly difficult to export their MATLAB/Octave models to SBML.

The goal of this project is to develop software that uses a combination of heuristics and user assistance to help researchers export models written as ordinary MATLAB and Octave scripts. MOCCASIN (*"Model ODE Converter for Creating Automated SBML INteroperability"*) helps researchers take ODE (ordinary differential equation) models written in MATLAB and Octave and export them as SBML files.  Although its scope is limited to MATLAB written with certain assumptions, and general conversion of MATLAB models is impossible, MOCCASIN nevertheless *can* translate some common forms of models into SBML.

MOCCASIN is written in Python and does _not_ require MATLAB to run.


✺ How it works
------------

MOCCASIN parses MATLAB files using a novel MATLAB parser developed by the authors and written entirely in Python.  It applies post-processing operations in order to interpret the MATLAB contents, then uses a network service provided by the [Biochemical Abstract Machine (BIOCHAM)](https://lifeware.inria.fr/biocham/) to invoke an algorithm developed by Fages, Gay and Soliman described in their 2015 paper titled [_Inferring reaction systems from ordinary differential equations_](http://www.sciencedirect.com/science/article/pii/S0304397514006197).  (A free technical report explaining the algorithm is [available from INRIA](https://hal.inria.fr/hal-01103692).)  Finally, it applies some post-processing to the results returned by BIOCHAM to produce the completed SBML output.

Currently, MOCCASIN is limited to MATLAB inputs in which a model is contained in a single file.  The file must set up a system of differential equations as a function defined in the file, and make a call to one of the MATLAB `odeNN` family of solvers (e.g., `ode45`, `ode15s`, etc.).  The following is a simple but complete example:

```matlab
% Various parameter settings.  The specifics here are unimportant; this
% is just an example of a real input file.
%
tspan  = [0 300];
xinit  = [0; 0];
a      = 0.01 * 60;
b      = 0.0058 * 60;
c      = 0.006 * 60;
d      = 0.000192 * 60;

% A call to a MATLAB ODE solver
%
[t, x] = ode45(@f, tspan, xinit);

% A function that defines the ODEs of the model.
%
function dx = f(t, x)
  dx = [a - b * x(1); c * x(1) - d * x(2)];
end
```

You can view the SBML output for this example [in a separate file](docs/project/examples/example.xml).  MOCCASIN assumes that the second parameter in the ODE function definition determines the variables that identify the SBML species; thus, the output generated by MOCCASIN will have SBML species named `x_1` and `x_2` by default.  (The use of suffixes is necessary because plain SBML does not support arrays or vectors.)  The output will also not capture any information about the particular ODE solver or the start/stop/configuration parameters used in the file, because that kind of information is not meant to be stored in SBML files anyway.  (A future version of MOCCASIN will hopefully translate the additional run information into [SED-ML](http://sed-ml.org) format.)

Because MOCCASIN does not currently implement the Fages, Gay and Soliman algorithm internally, it requires a network connection during operation so that it can contact the [(BIOCHAM)](https://lifeware.inria.fr/biocham/) service.


☛ Installation and configuration
--------------------------------

As of version 1.3, MOCCASIN is distributed as a standalone self-contained program.  Users no longer need to install Python (although running MOCCASIN as a Python program still remains an option).


### _Preferred approach: download and install the self-contained program_

To obtain a copy of MOCCASIN, please select the appropriate version from the following table.  If you do not see your operating listed below, please [contact us](mailto:moccasin-dev@googlegroups.com) and we may be able to create an appropriate version for you.

| Operating System           | Download                            | Post-download instructions | Note | 
|----------------------------|-------------------------------------|--------------|:-------:| 
| macOS 10.13 (High Sierra)  | [MOCCASIN-1.3.0-macos-10.13.pkg](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-macos-10.13.pkg)  | Double-click the `.pkg` file | (a) |
| macOS 10.12 (Sierra)       | [MOCCASIN-1.3.0-macos-10.12.pkg](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-macos-10.12.pkg)  | Double-click the `.pkg` file | (a) | 
| Ubuntu Linux 18.x          | [MOCCASIN-1.3.0-ubuntu-18.04.tar.gz](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-ubuntu-18.04.tar.gz) | Uncompress &amp; untar the `.tar.gz` | (b) |
| Ubuntu Linux 16.x          | [MOCCASIN-1.3.0-ubuntu-16.04.tar.gz](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-ubuntu-16.04.tar.gz) | Uncompress &amp; untar the `.tar.gz` | (b) |
| CentOS Linux 7.5           | [MOCCASIN-1.3.0-centos-7.5.tar.gz](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-centos-7.5.tar.gz) | Uncompress &amp; untar the `.tar.gz` | (b) |
| CentOS Linux 7.4           | [MOCCASIN-1.3.0-centos-7.4.tar.gz](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-centos-7.4.tar.gz) | Uncompress &amp; untar the `.tar.gz` | (b) |
| Windows 10 64-bit          | [MOCCASIN-1.3.0-win-10-x64.zip](https://github.com/sbmlteam/moccasin/releases/download/1.3.0/MOCCASIN-1.3.0-win-10-x64.exe) | Double-click the `.exe` | (c) |

Notes:

(a) The installer will create a folder in `/Applications` where it will place the `MOCCASIN` graphical application; it will also put a command-line program named `moccasin` in `/usr/local/bin/`.

(b) There is no MOCCASIN installer program for Linux.  The `.tar.gz` archive simply contains a single program, `moccasin`, that can be used both to start the graphical interface and to use MOCCASIN via the command line.  Move `moccasin` to a suitable `bin` directory on your computer and run it from there.

(c) The installer is a typical Windows installer program. Save the file somewhere on your computer, double-click the file to run the installer, and follow the directions.

After installation, please proceed to the section below titled [Using MOCCASIN](#-using-moccasin) for further instructions.


### _Alternative approach: run MOCCASIN as a typical Python program_

MOCCASIN requires Python version 3.4 or higher, and depends on other Python packages such as [wxPython](https://wxpython.org).  Installing the necessary dependencies can be a difficult process.  We provide instructions in the wiki.

After you have installed the third-party libraries that MOCCASIN depends upon, proceed to install MOCCASIN. The following is probably the simplest and most direct way:
```sh
sudo python3 -m pip install git+https://github.com/sbmlteam/moccasin.git
```

Alternatively, you can clone this GitHub repository to a location on your computer's file system and then run `setup.py`:
```sh
git clone https://github.com/sbmlteam/moccasin.git
cd moccasin
sudo python3 -m pip install .
```


► Using MOCCASIN
--------------

You can use MOCCASIN either via the command line or via a graphical user interface (GUI).  (Note that in both cases, as mentioned above, MOCCASIN needs a network connection to perform its work.)


### _The graphical user interface_

To run the GUI version, you typically start MOCCASIN like most ordinary programs on your computer (e.g., by double-clicking the icon).  Once the GUI window opens, the first thing you will probably want to do is click the *Browse* button in the upper right of the window, to find the MATLAB file you want to convert on your computer.  Once you do this, you can select a few options, and click the *Convert* button.  After some time (depending on the size of the file), you should eventually get SBML output in the lowest panel of the GUI.  The animation below illustrates the whole process:

<p align="center">
<img src="https://cloud.githubusercontent.com/assets/1450019/16715437/44c33744-4694-11e6-9f81-ebbe64788ac1.gif" alt="MOCCASIN GUI" title="MOCCASIN GUI"/>
</p>

MOCCASIN offers a few conversion options:

* It can generate equation-based SBML output instead of the default, which is reaction-based SBML.  The former uses no reactions, and instead writes out everything in terms of SBML "rate rules".

* It can encode variables as SBML parameters instead of the default, to encode them as SBML species.  Depending on your application and what you do with the output, this may or may not be useful.

* It can generate XPP `.ode` file output, instead of SBML format.


### _The command-line interface_


The MOCCASIN installer _should_ also place a new command-line program on your shell's search path, so that you can start MOCCASIN with a simple shell command:
```
moccasin
```

To use the command-line interface, supply one or more MATLAB files on the command line; MOCCASIN will read and convert the file(s):
```
moccasin matlabfile.m
```

It also accepts additional command-line arguments.  To get information about the other options, use the `-h` argument (or `/h` on Windows):
```
moccasin -h
```


⁇ Getting help and support
--------------------------

MOCCASIN is under active development by a distributed team.  If you have any questions, please feel free to post or email on the developer's discussion group  ([https://groups.google.com/forum/#!forum/moccasin-dev](https://groups.google.com/forum/#!forum/moccasin-dev)) or contact the main developers directly.


★ Do you like it?
------------------

If you like this software, don't forget to give this repo a star on GitHub to show your support!


♬ Contributing &mdash; info for developers
------------------------------------------

A lot remains to be done on MOCCASIN in many areas, from improving the interpretation of MATLAB to adding support for SED-ML.  We would be happy to receive your help and participation if you are interested.  Please feel free to contact the developers.

A quick way to find out what is currently on people's plates and our near-term plans is to look at the [GitHub issue tracker](https://github.com/sbmlteam/moccasin/issues) for this project.

Everyone is asked to read and respect the [code of conduct](CONDUCT.md) when participating in this project.


☺︎ Acknowledgments
-----------------------

Continuing work on MOCCASIN is made possible thanks to funding from the [National Institutes of Health](https://nih.gov) (NIH) via [NIGMS](https://www.nigms.nih.gov/Pages/default.aspx) grant number GM070923 (principal investigator: Michael Hucka).  This software was originally developed thanks in part to funding from the Icahn School of Medicine at Mount Sinai, provided as part of the NIH-funded project *Modeling Immunity for Biodefense* (contract number HHSN266200500021C, Principal Investigator: [Stuart Sealfon](http://www.mountsinai.org/profiles/stuart-c-sealfon)), and in part to funding from the School of Medicine at Boston University, provided as part of the NIH-funded project *Modeling Immunity for Biodefense* (contract number HHSN272201000053C, Principal Investigators: [Thomas B. Kepler](http://www.bu.edu/computationalimmunology/people/thomas-b-kepler/) and [Garnett H. Kelsoe](http://immunology.duke.edu/faculty/details/0205291)).

We also acknowledge the contributions made by Dr. [Dagmar Iber](http://www.silva.bsse.ethz.ch/cobi/people/iberd) from the Department of Biosystems Science and Engineering (D-BSSE), and Dr. [Bernd Rinn](https://www1.ethz.ch/id/about/sections/sis/index_EN) from the Scientific IT Services (SIS) division from ETH Zurich.

The MOCCASIN logo was created by Randy Carlton (<rcarlton@rancar2.com>).


☮︎ Copyright and license
---------------------

Copyright (C) 2014-2018 jointly by the California Institute of Technology (Pasadena, California, USA), the Icahn School of Medicine at Mount Sinai (New York, New York, USA), and Boston University (Boston, Massachusetts, USA).

This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or any later version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and documentation provided hereunder is on an "as is" basis, and the California Institute of Technology has no obligations to provide maintenance, support, updates, enhancements or modifications.  In no event shall the California Institute of Technology be liable to any party for direct, indirect, special, incidental or consequential damages, including lost profits, arising out of the use of this software and its documentation, even if the California Institute of Technology has been advised of the possibility of such damage.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this library in the file named "COPYING.txt" included with the software distribution.

<br>
<div align="center">
  <a href="https://www.nigms.nih.gov">
    <img valign="middle"  height="100" src=".graphics/US-NIH-NIGMS-Logo.svg">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.caltech.edu">
    <img valign="middle"  width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.nsf.gov">
    <img valign="middle"  height="115" src=".graphics/MSMC_Icahn.jpg">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.nsf.gov">
    <img valign="middle" height="60" src=".graphics/Boston_University_wordmark.svg">
  </a>
</div>
