MOCCASIN News &ndash; History of user-visible changes
=====================================================

1.2.0
-----

There are three important changes in this release.  The first is a *massive* improvement to the speed of parsing MATLAB files compared to recent performance.  The second is the elimination of the separate `moccasin_CLI` and `moccasin_GUI` entry points in favor of a single program, `moccasin`, that can be used either to start the GUI or perform actions via the command line.  The third is corretions of errors in the installation scripts so that `setup.py` now correctly installs dependencies.

Enhancements:

* New command-line driver interface called, simply, `moccasin`.  It features a revised set of command-line options, snazzy colors, spinners and more!

* A past enhancement to `setup.py` caused it to stop being able to install dependencies normally, with the consequence that users had to install dependent Python packages by hand.  This was problematic in many cases because the packages were not always easily installed.  The errors in `setup.py` have been corrected.

* The installation instructions have been updated and improved.

* The GUI interface provides (hopefully) more helpful dialogs.

* Huge performance improvements.


Bug fixes:

* [#49](https://github.com/sbmlteam/moccasin/issues/49) Fixed extreme slowness of MATLAB parser.

* [#46](https://github.com/sbmlteam/moccasin/issues/46) Fix for moccasin GUI not launching.

* [#51](https://github.com/sbmlteam/moccasin/issues/51) Fixed bugs in checking whether MATLAB input is translatable, and add support for use of element-wise operators such as `.*` when they are not actually being used on matrices.

* [#52](https://github.com/sbmlteam/moccasin/issues/52) Fixed bug in writing out very large numbers. Thanks to user [@willigot](https://github.com/sbmlteam/moccasin/issues/created_by/willigott) for reporting the issue.

* [#53](https://github.com/sbmlteam/moccasin/issues/53) Biocham currently seems to mistranslate unary negation, at least in some situations.  MOCCASIN now has a workaround that replaces expressions of the form `-x` with `-1 * x`, which works better when passed to Biocham.  This is hopefully temporary, until Biocham has a chance to address whatever the underlying issue is.  Many thanks to user [@willigot](https://github.com/sbmlteam/moccasin/issues/created_by/willigott) for reporting the issue and suggesting the workaround.


1.1.2
----------

Release 1.1.2 fixes a bug that caused MOCCASIN to fail on some scripts that did not have an enclosing function.  Issues resolved: #19, #20.



1.1.1
----------

This release fixes compatibility issues with wxPython version 1.1.1.



1.1.0
----------

This release features a major overhaul of the underlying MATLAB parser, as well as a substantial rewrite of the SBML/XPP converter code. The new system is much more robust in the face of a greater range of MATLAB inputs, although the types of MATLAB models it recognizes and can convert are still relatively limited.

The new MATLAB parser correctly parses much more of the MATLAB syntax, thus eliminating many previous parsing errors and failures. There are now hundreds of new test cases for different syntactic forms of MATLAB. The known cases of MATLAB syntax that are not yet handled are only the following:

* user-defined classes are not yet supported at all

* cell arrays are parsed in a limited way, and in particular, nested cell array references will fail

* commas and spaces cannot be mixed in a row of an array: e.g., `[1, 2 -3 +4]` will fail to parse as expected

* comments inside arrays are discarded

* comments after continuations are discarded

* continuations (i.e., `...`) inside strings will cause the strings to be mangled

* continuations in shell commands are not handled correctly

The MATLAB parser also implements a weak, heuristic form of "kind" analysis to try to disambiguate function calls from array references (which in MATLAB are syntactically identical). The inability of MOCCASIN to access the user's MATLAB environment makes it impossible for MOCCASIN to ever be able to do full kind analysis, but the heuristics take it very far for many use-cases in MOCCASIN's domain.

The update converter is more robust for more cases, and reports many more errors and failures of conversion. It takes advantage of more features of the XPP input syntax handled by BIOCHAM, allowing the final converted SBML output to be a more faithful representation of the input model. However, the scope of models it can convert has only widened slightly – the converter is not yet able to convert a greater range of MATLAB models than it did before. Handling a wider range of MATLAB inputs will require implementing solutions to such things as handling loops, handling if statements, loading .mat files, and converting array variables into scalar variables so that they can be expressed in SBML (which does not yet support array variables).

Despite these limitations, the converter is able to convert significant real-world models. As an example of the capabilities of MOCCASIN 1.1.0, it was used to convert model BIOMD0000000608 in BioModels Database. The original MATLAB model is 770 lines long and the converted form has 140 SBML reactions.



1.0.0
----------

First release.




<!--
# The following is for [X]Emacs users.  Please leave in place.
# Local Variables:
# fill-column: 70
# End:
-->
