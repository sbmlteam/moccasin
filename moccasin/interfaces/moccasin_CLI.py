#!/usr/bin/env python3
#
# @file    moccasin.py
# @brief   Command-line interface for Moccasin
# @author  Michael Hucka
# @author  Harold Gomez
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2018 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Icahn School of Medicine at Mount Sinai, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

import plac
import sys
import os
try:
    from termcolor import colored
except:
    pass
import time

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '../..'))
except:
    sys.path.append('../..')

import moccasin
from moccasin.interfaces import moccasin_GUI
from .controller import Controller
from .network_utils import have_network

# This prevents exceeding recursion depth in some cases.
sys.setrecursionlimit(5000)


# -----------------------------------------------------------------------------
# Main body.
# -----------------------------------------------------------------------------

# Argument annotations: (help, kind, abbrev, type, choices, metavar)
@plac.annotations(
    gui           = ('start GUI interface (ignores other arguments)',          'flag', 'g'),
    use_equations = ('create equation-based SBML (default: reaction-based)',   'flag', 'e'),
    use_params    = ('encode variables as SBML parameters (default: species)', 'flag', 'p'),
    quiet         = ('do not print informational messages while working',      'flag', 'q'),
    relaxed       = ('assume certain MATLAB operators are not used in input',  'flag', 'r'),
    xpp_output    = ('create XPP ODE format instead of SBML format output',    'flag', 'x'),
    no_color      = ('do not color-code the terminal output (default: do)',    'flag', 'C'),
    debug_parser  = ('print debug information about the parsed MATLAB',        'flag', 'D'),
    version       = ('print MOCCASIN version info and exit',                   'flag', 'V'),
    no_comments   = ('do not insert version comments into SBML output',        'flag', 'X'),
    paths         = 'paths to MATLAB input files to convert'
)

def cli_main(gui, use_equations, use_params, quiet, relaxed, xpp_output,
             no_color, debug_parser, version, no_comments, *paths):
    '''Interface for controlling MOCCASIN, the MATLAB ODE converter for SBML.
MOCCASIN can take certain forms of ODE (ordinary differential equation) models
written in MATLAB and Octave and export them as SBML files.  MOCCASIN does not
require MATLAB -- it contains its own parser and translation code.

If given no arguments at all, or if given the command-line option --gui, this
program will start the graphical interface to MOCCASIN and ignore all other
arguments.  If given the argument -v, it will print information about the
current program version, and exit.  Otherwise, this program expects at least
one file name as an argument.  MOCCASIN will convert each given file, saving
the results in the same file path but with the extension ".xml".  (That is,
if given the file "model.m", it will produce "model.xml".)

Currently, MOCCASIN is limited to inputs in which the model is self-contained
in a single file and not split across multiple files.  (In other words, each
file given as argument must represent a single model.)  The MATLAB file must
set up a system of differential equations as a function defined in the file,
and make a call to one of the MATLAB "odeNN" family of solvers (e.g.,
"ode45", "ode15s", etc.).  The following is a simple but complete example:

    % Various parameter settings:

    tspan  = [0 300];
    xinit  = [0; 0];
    a      = 0.01 * 60;
    b      = 0.0058 * 60;
    c      = 0.006 * 60;
    d      = 0.000192 * 60;

    % A call to a MATLAB ODE solver:

    [t, x] = ode45(@f, tspan, xinit);

    % A function that defines the ODEs of the model:

    function dx = f(t, x)
      dx = [a - b * x(1); c * x(1) - d * x(2)];
    end

MOCCASIN assumes that the second parameter in the ODE function definition
determines the variables that should identify the SBML species; thus, the
output generated by MOCCASIN will have SBML species named "x_1" and "x_2" by
default.  (The use of suffixes is necessary because plain SBML does not
support arrays or vectors.)  The output will also not capture any information
about the particular ODE solver or the start/stop/configuration parameters
used in the file, because that kind of information is not meant to be stored
in SBML files anyway.

The converter can only handle a very limited subset of MATLAB constructs.  A
notable class of constructs it cannot handle is matrix/array operators in
equations such as the element-wise equivalents of addition, subtraction, and
similar.  Since MATLAB users sometimes employ the operators in their formulas
even when they do not need to, MOCCASIN can be told to assume non-matrix
meanings of .*, .^, etc. using the argument -r.

This command-line interface understands some additional arguments controlling
the translation process:

  -e  makes the translator create equation-based SBML output, instead of
      the default, which is to convert the model to reaction-based form

  -p  makes the translator encode variables as SBML parameters, instead of
      the default, which is to use SBML species

  -x  makes the translator create XPP ODE files instead of SBML output

  -V  omits the comments that are inserted into the SBML file by default to
      record the MOCCASIN version used to create the file

For more information about SBML, please visit https://sbml.org
For more information about MOCCASIN, visit https://sbml.org/Software/MOCCASIN

MOCCASIN is an acronym for "Model ODE Converter for Creating Automated
SBML INteroperability".
'''

    # Process arguments.

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not no_color
    add_comments = not no_comments

    if gui or not any([paths, use_equations, use_params, xpp_output,
                       version, debug_parser, quiet, no_comments]):
        moccasin_GUI.gui_main()
        sys.exit()
    if version:
        msg('MOCCASIN version {}'.format(moccasin.__version__))
        msg('Author: {}'.format(moccasin.__author__))
        msg('E-mail: {}'.format(moccasin.__email__))
        msg('URL: {}'.format(moccasin.__url__))
        msg('License: {}'.format(moccasin.__license__))
        msg('Citation: {}'.format(moccasin.__citation__))
        sys.exit()
    if not paths:
        raise SystemExit(color('Must provide a path to a file.', 'error', colorize))
    if not xpp_output and not use_equations and not have_network():
        raise SystemExit(color('No network connection.', 'error', colorize))
    if not quiet:
        from halo import Halo
    extension = '.ode' if xpp_output else '.xml'

    # Define helper function used below.

    def convert(path):
        controller = Controller()
        contents = file_contents(path, colorize)
        if debug_parser:
            print_header('{}'.format(path), 'info', quiet, colorize)
            msg(contents)
        if not debug_parser and not quiet:
            msg('Parsing MATLAB file "{}" ...'.format(path), 'info', colorize)
        controller.parse_contents(contents)
        controller.check_translatable(relaxed)
        if debug_parser:
            print_header('Parsed MATLAB output', 'info', quiet, colorize)
            msg(controller.print_parsed_results())
        elif not quiet:
            msg('... finished.', 'info', colorize)
            msg('Converting to {} ...'.format('XPP' if xpp_output else 'SBML'),
                'info', colorize)
        if xpp_output:
            text = 'XPP output'
            output = controller.build_model(use_species = (not use_params),
                                            output_format = "xpp",
                                            name_after_param = False,
                                            add_comments = add_comments)
        elif use_equations:
            text = 'Equation-based SBML output'
            output = controller.build_model(use_species = (not use_params),
                                            output_format = "sbml",
                                            name_after_param = False,
                                            add_comments = add_comments)
        else:
            text = 'Reaction-based SBML output'
            output = controller.build_reaction_model(use_species = (not use_params),
                                                     name_after_param = False,
                                                     add_comments = add_comments)
        if debug_parser:
            print_header(text, 'info', quiet, colorize)
            msg(output)
        else:
            if not quiet:
                msg('... finished.', 'info', colorize)
            output_path = os.path.splitext(path)[0] + extension
            backup_path = output_path + '.bak'
            if os.path.exists(output_path):
                if not quiet:
                    msg('Output file "{}" already exists.'.format(output_path),
                        'warning', colorize)
                    msg('Renaming to "{}".'.format(backup_path),
                        'warning', colorize)
                os.rename(output_path, backup_path)
            with open(output_path, 'w') as output_file:
                output_file.write(output)
            if not quiet:
                msg('Wrote output to "{}"'.format(output_path), 'info', colorize)

    # Loop over the input files and process each one.

    for path in paths:
        if not os.path.exists(path):
            msg('File "{}" does not appear to exist.'.format(path), 'error', colorize)
            continue
        elif not os.path.isfile(path):
            msg('File "{}" does not appear to be a file.'.format(path), 'error', colorize)
            continue
        try:
            if debug_parser:
                convert(path)
            else:
                prefix = color('{} '.format(path), 'info', colorize)
                if colorize:
                    if sys.platform.startswith('linux'):
                        # The following is an ugly hack to resolve the error
                        # "'ascii' code can't encode character .... ordinal
                        # not in range(128)" on Linux when the environment
                        # variable LC_ALL defaults to C.  Setting the locale
                        # within Python didn't work.  We can't ask the users
                        # to set LC_ALL to 'en_US.UTF-8'. The following did it.
                        sys.stdout = open(sys.stdout.fileno(), mode='w',
                                          encoding='utf8', buffering=1)
                    with Halo(spinner='bouncingBall', enabled = not quiet):
                        init_halo_hack()
                        convert(path)
                else:
                    convert(path)
                if len(paths) > 1 and not quiet:
                    msg('-'*70, 'info', colorize)

        except IOError as err:
            msg('Error reading file "{}": {}'.format(path, err), 'error', colorize)
            continue
        except Exception as err:
            msg("Error: {0}".format(err), 'error', colorize)
            sys.exit()


# -----------------------------------------------------------------------------
# Helper functions.
# -----------------------------------------------------------------------------

def file_contents(path, colorize):
    try:
        with open(path) as input_file:
            return input_file.read()
    except Exception as err:
        raise


def print_header(text, flags, quiet = False, colorize = True):
    if not quiet:
        msg('')
        msg('{:-^78}'.format(' ' + text + ' '), flags, colorize)
        msg('')


def msg(text, flags = None, colorize = True):
    '''Like the standard print(), but flushes the output immediately and
    colorizes the output by default. Flushing immediately is useful when
    piping the output of a script, because Python by default will buffer the
    output in that situation and this makes it very difficult to see what is
    happening in real time.
    '''
    if colorize:
        print(color(text, flags), flush = True)
    else:
        print(text, flush = True)


def color(text, flags = None, colorize = True):
    (prefix, color_name, attributes) = color_codes(flags)
    if colorize:
        if attributes and color_name:
            return colored(text, color_name, attrs = attributes)
        elif color_name:
            return colored(text, color_name)
        elif attributes:
            return colored(text, attrs = attributes)
        else:
            return text
    elif prefix:
        return prefix + ': ' + text
    else:
        return text


def color_codes(flags):
    color_name  = ''
    prefix = ''
    attrib = []
    if type(flags) is not list:
        flags = [flags]
    if 'error' in flags:
        prefix = 'ERROR'
        color_name = 'red'
    if 'warning' in flags:
        prefix = 'WARNING'
        color_name = 'yellow'
    if 'info' in flags:
        color_name = 'green'
    if 'white' in flags:
        color_name = 'white'
    if 'blue' in flags:
        color_name = 'blue'
    if 'grey' in flags:
        color_name = 'grey'
    if 'cyan' in flags:
        color_name = 'cyan'
    if 'underline' in flags:
        attrib.append('underline')
    if 'bold' in flags:
        attrib.append('bold')
    if 'reverse' in flags:
        attrib.append('reverse')
    if 'dark' in flags:
        attrib.append('dark')
    return (prefix, color_name, attrib)


# init_halo_hack() is mostly a guess at a way to keep the first part of the
# spinner printed by Halo from overwriting part of the first message we
# print.  It seems to work, but the problem that this tries to solve occurred
# sporadically anyway, so maybe the issue still remains and I just haven't
# seen it happen again.

def init_halo_hack():
    '''Write a blank to prevent occasional garbled first line printed by Halo.'''
    sys.stdout.write('')
    sys.stdout.flush()
    time.sleep(0.1)


# Please leave the following for Emacs users.
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
