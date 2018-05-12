MOCCASIN
========

<img align="right" src="https://raw.githubusercontent.com/sbmlteam/moccasin/master/docs/project/logo/moccasin_logo_20151002/logo_128.png"> *MOCCASIN* stands for *"Model ODE Converter for Creating Automated SBML INteroperability"*.  MOCCASIN is designed to convert certain basic forms of ODE simulation models written in MATLAB or Octave and translate them into [SBML](http://sbml.org) format.  It thereby enables researchers to convert MATLAB models into an open and widely-used format in systems biology.

[![License](http://img.shields.io/:license-LGPL-blue.svg)](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html)  [![Latest version](https://img.shields.io/badge/Latest_version-1.2.0-brightgreen.svg)](http://shields.io) <!--
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.883135.svg)](https://doi.org/10.5281/zenodo.883135)--> [![Build Status](https://travis-ci.org/sbmlteam/moccasin.svg?branch=master)](https://travis-ci.org/sbmlteam/moccasin) [![Coverage Status](https://coveralls.io/repos/sbmlteam/moccasin/badge.svg?branch=master)](https://coveralls.io/r/sbmlteam/moccasin?branch=master)

*Authors*:      [Michael Hucka](http://www.cds.caltech.edu/~mhucka), [Sarah Keating](http://www.ebi.ac.uk/about/people/sarah-keating), and [Harold G&oacute;mez](http://www.bu.edu/computationalimmunology/people/harold-gomez/).<br>
*License*:      This code is licensed under the LGPL version 2.1.  Please see the file [../LICENSE.txt](https://raw.githubusercontent.com/sbmlteam/moccasin/master/LICENSE.txt) for details.<br>
*Code repository*:   [https://github.com/sbmlteam/moccasin](https://github.com/sbmlteam/moccasin)<br>
*Developers' discussion group*: [https://groups.google.com/forum/#!forum/moccasin-dev](https://groups.google.com/forum/#!forum/moccasin-dev)

🏁 Recent news and activities
------------------------------

_May 2018_: Release 1.2.0 includes a fix for a critical performance bug caused by a change to the API in PyParsing, with the consequence that MOCCASIN should run an order of magnitude faster than the last release.  Additional changes include several important bug fixes, improvements to the installation instructions, and improved diagnostics in the GUI interface.  Please see the [NEWS.md](NEWS.md) file for more details.

Table of Contents
-----------------

* [Please cite the MOCCASIN paper and the version you use](#️-please-cite-the-moccasin-paper-and-the-version-you-use)
* [Background and introduction](#-background-and-introduction)
* [How it works](#-how-it-works)
* [Installation and configuration](#-installation-and-configuration)
    * [<em>Check and install dependencies</em>](#-check-and-install-dependencies)
    * [<em>Download and install MOCCASIN</em>](#-download-and-install-moccasin)
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

* MOCCASIN release 1.1.2 &rArr; [10.5281/zenodo.883135](https://doi.org/10.5281/zenodo.883135)

☀ Background and introduction
-----------------------------

Computational modeling has become a crucial aspect of biological research, and [SBML](http://sbml.org) (the Systems Biology Markup Language) has become the de facto standard open format for exchanging models between software tools in systems biology. [MATLAB](http://www.mathworks.com) and [Octave](http://www.gnu.org/software/octave/) are popular numerical computing environments used by modelers in biology, but while toolboxes for using SBML exist, many researchers either have legacy models or do not learn about the toolboxes before starting their work and then find it discouragingly difficult to export their MATLAB/Octave models to SBML.

The goal of this project is to develop software that uses a combination of heuristics and user assistance to help researchers export models written as ordinary MATLAB and Octave scripts. MOCCASIN (*"Model ODE Converter for Creating Automated SBML INteroperability"*) helps researchers take ODE (ordinary differential equation) models written in MATLAB and Octave and export them as SBML files.  Although its scope is limited to MATLAB written with certain assumptions, and general conversion of MATLAB models is impossible, MOCCASIN nevertheless *can* translate some common forms of models into SBML.

MOCCASIN is written in Python and does _not_ require MATLAB to run.  It requires [libSBML](http://sbml.org/Software/libSBML) and a number of common Python 3 libraries to run.

✺ How it works
------------

MOCCASIN uses an algorithm developed by Fages, Gay and Soliman described in their 2015 paper titled [_Inferring reaction systems from ordinary differential equations_](http://www.sciencedirect.com/science/article/pii/S0304397514006197).  A free technical report explaining the algorithm is [available from INRIA](https://hal.inria.fr/hal-01103692).  To parse MATLAB and produce input to the reaction-inference algorithm, MOCCASIN uses a custom MATLAB parser written using [PyParsing](https://pyparsing.wikispaces.com) and a variety of post-processing operations to interpret the MATLAB contents.

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


☛ Installation and configuration
--------------------------------

MOCCASIN requires Python version 3 and depends on numerous other Python packages.

## ⓵&nbsp;&nbsp; _Check and install dependencies_

Most dependent packages should install automatically using Python `pip` and PyPI, but some of those packages themselves have dependencies on system libraries that may require separate manual installation.  The following is a guide for the systems we have tested.

### Ubuntu Linux 14.x and 16.x

The basic installation of Ubuntu Linux does not come with Python, `pip` or `git`, so they need to be installed.  In addition, wxPython needs numerous libraries to be installed first, or the installation of wxPython itself (during the installation of MOCCASIN) will fail.  The following shell commands should get the necessary things installed:

```
sudo apt-get install -y git python3-pip build-essential libtiff5-dev freeglut3-dev libsdl2-dev
sudo apt-get install -y libgstreamer-plugins-base1.0-dev libwebkit2gtk-4.0-dev 
```

After this is finished, the steps to download and install MOCCASIN should work.

### macOS

For recent versions of macOS such as 10.13 (High Sierra), you will need  [Xcode](https://itunes.apple.com/us/app/xcode/id497799835?mt=12) from the Apple App Store.  You will also need to install the command-line tools, which can be done using the following shell command:
```
sudo xcode-select --install
```

Finally, you will also to install Python&nbsp;3 and `pip`.  If you use [MacPorts](https://www.macports.org), you could use the following sequence of commands:
```
sudo port install python34 py34-pip
sudo port select --set python3 python34
```

After this, the steps to download and install MOCCASIN should work.

### CentOS 7

Python&nbsp;3 and `pip`, as well as development tools such as a compiler, first need to be installed:

```csh
sudo yum -y install epel-release
sudo yum -y install python34-setuptools python34-pip
sudo yum -y install groupinstall development
```

Next, installing wxPython is the most difficult step.  If at all possible, find an existing wheel file.  For CentOS&nbsp;7, the site [https://extras.wxpython.org/wxPython4/extras/linux/gtk3/centos-7/](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/centos-7/) contains recent builds in Python wheel format.  Download the latest version that matches your Python configuration.  For example, at the time of this writing, the most recent version of wxPython is 4.0.1 and the wheel file for Python&nbsp;3.4 is named [wxPython-4.0.1-cp34-cp34m-linux_x86_64.whl](https://extras.wxpython.org/wxPython4/extras/linux/gtk3/centos-7/wxPython-4.0.1-cp34-cp34m-linux_x86_64.whl). Download the wheel file to a temporary location on your computer and then run the following command:
```csh
sudo python3 -m pip install /path/to/wxPython-4.0.1-cp34-cp34m-linux_x86_64.whl
```

After that, the steps below to download and install MOCCASIN should work.  If you cannot get wxPython installed using a prebuilt wheel, then please consult the [wxPython build information  page](https://wxpython.org/pages/downloads/index.html) or contact the MOCCASIN developers.

## ⓶&nbsp;&nbsp; _Download and install MOCCASIN_

The following is probably the simplest and most direct way to install MOCCASIN on your computer:
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

You can use MOCCASIN either via the command line or via a built-in GUI interface.  Both interface area accessed using the same command, with the default being to start the GUI interface.  On Linux and macOS systems, the installation _should_ place a new program on your shell's search path, so that you can start MOCCASIN with a simple shell command:
```
moccasin
```

If that fails because the shell cannot find the command, you should be able to run it using the alternative approach:
```
python3 -m moccasin
```

To use the command-line interface, supply one or more MATLAB files on the command line; MOCCASIN will read and convert the file(s):
```
moccasin path/to/a/matlab/file.m
```

It also accepts additional command-line arguments.  To get information about the other options, use the `-h` argument:
```
moccasin -h
```

Once the GUI window opens, the first thing you will probably want to do is click the *Browse* button in the upper right of the window, to find the MATLAB file you want to convert on your computer.  Once you do this, you can select a few options, and click the *Convert* button.  After some time (depending on the size of the file), you should eventually get SBML output in the lowest panel of the GUI.  The animation below illustrates the whole process:

<p align="center">
<img src="https://cloud.githubusercontent.com/assets/1450019/16715437/44c33744-4694-11e6-9f81-ebbe64788ac1.gif" alt="MOCCASIN GUI" title="MOCCASIN GUI"/>
</p>

MOCCASIN offers a few conversion options:

* It can generate equation-based SBML output instead of the default, which is reaction-based SBML.  The former uses no reactions, and instead writes out everything in terms of SBML "rate rules".

* It can encode variables as SBML parameters instead of the default, to encode them as SBML species.  Depending on your application and what you do with the output, this may or may not be useful.

* It can generate XPP `.ode` file output, instead of SBML format.


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


☺ Acknowledgments
-----------------------

This work is made possible thanks in part to funding from the Icahn School of Medicine at Mount Sinai, provided as part of the NIH-funded project *Modeling Immunity for Biodefense* (contract number HHSN266200500021C)  (Principal Investigator: [Stuart Sealfon](http://www.mountsinai.org/profiles/stuart-c-sealfon)), and in part to funding from the School of Medicine at Boston University, provided as part of the NIH-funded project *Modeling Immunity for Biodefense* (contract number HHSN272201000053C)  (Principal Investigators: [Thomas B. Kepler](http://www.bu.edu/computationalimmunology/people/thomas-b-kepler/) and [Garnett H. Kelsoe](http://immunology.duke.edu/faculty/details/0205291)).

We also acknowledge the contributions made by Dr. [Dagmar Iber](http://www.silva.bsse.ethz.ch/cobi/people/iberd) from the Department of Biosystems Science and Engineering (D-BSSE), and Dr. [Bernd Rinn](https://www1.ethz.ch/id/about/sections/sis/index_EN) from the Scientific IT Services (SIS) division from ETH Zurich.

The MOCCASIN logo was created by Randy Carlton (<rcarlton@rancar2.com>).


☮ Copyright and license
---------------------

Copyright (C) 2014-2017 jointly by the California Institute of Technology (Pasadena, California, USA), the Icahn School of Medicine at Mount Sinai (New York, New York, USA), and Boston University (Boston, Massachusetts, USA).

This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or any later version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and documentation provided hereunder is on an "as is" basis, and the California Institute of Technology has no obligations to provide maintenance, support, updates, enhancements or modifications.  In no event shall the California Institute of Technology be liable to any party for direct, indirect, special, incidental or consequential damages, including lost profits, arising out of the use of this software and its documentation, even if the California Institute of Technology has been advised of the possibility of such damage.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this library in the file named "COPYING.txt" included with the software distribution.
