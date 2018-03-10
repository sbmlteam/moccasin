#!/usr/bin/env python3
#
# @file    moccasin.py
# @brief   Command-line interface for Moccasin
# @author  Harold Gomez
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Automated SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014-2017 jointly by the following organizations:
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

from __future__ import print_function
import plac
import sys
import os
try:
    from termcolor import colored
except:
    pass

try:
    thisdir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(thisdir, '..'))
except:
    sys.path.append('..')

from controller import Controller

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
    xpp_output    = ('create XPP ODE format instead of SBML format output',    'flag', 'x'),
    version       = ('print MOCCASIN version info and exit',                   'flag', 'v'),
    no_color      = ('do not color-code the terminal output (default: do)',    'flag', 'C'),
    debug_parser  = ('print debug information about the parsed MATLAB',        'flag', 'D'),
    no_comments   = ('do not insert version comments into SBML output',        'flag', 'V'),
    paths         = 'paths to MATLAB input files to convert'
)

def main(gui, use_equations, use_params, quiet, xpp_output, version,
         no_color, debug_parser, no_comments, *paths):
    '''Interface for controlling MOCCASIN, the MATLAB ODE converter for SBML.'''

    # Process arguments.

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not no_color
    add_comments = not no_comments

    if gui:
        import moccasin_GUI
        gui_main()
        sys.exit()
    if version:
        import __version__
        msg('{} version {}'.format(__version__.__title__, __version__.__version__))
        msg('Author: {}'.format(__version__.__author__))
        msg('URL: {}'.format(__version__.__url__))
        msg('License: {}'.format(__version__.__license__))
        sys.exit()
    if not paths:
        raise SystemExit(colorcode('Must provide a path to a file.', 'error'))
    if not xpp_output and not use_equations and not check_network_connection():
        raise SystemExit(colorcode('No network connection.', 'error'))
    if not quiet:
        from halo import Halo

    # Define helper function used below.

    def convert(path):
        controller = Controller()
        with open(path) as input_file:
            file_contents = input_file.read()
            if debug_parser:
                print_header('{}'.format(path), 'info', quiet, colorize)
                msg(file_contents)
            if not debug_parser and not quiet:
                msg('Parsing MATLAB file "{}" ...'.format(path), 'info', colorize)
            controller.parse_File(file_contents)
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
                output_path = os.path.splitext(path)[0] + '.xml'
                backup_path = output_path + '.bak'
                if os.path.exists(output_path):
                    if not quiet:
                        msg('Output file "{}" already exists.'.format(output_path),
                            'warning', colorize)
                        msg('Renaming to "{}".'.format(backup_path),
                            'warning', colorize)
                    os.rename(output_path, backup_path)
                if not quiet:
                    msg('Writing output to "{}"'.format(output_path), 'info', colorize)
                with open(output_path, 'w') as output_file:
                    output_file.write(output)
                if not quiet:
                    msg('Finished processing "{}".'.format(path), 'info', colorize)

    # Loop over the input files and process each one.

    for path in paths:
        if not os.path.exists(path):
            raise SystemExit(colorcode('File "{}" does not appear to exist.'.format(path),
                                       'error', colorize))
        elif not os.path.isfile(path):
            raise SystemExit(colorcode('File "{}" does not appear to be a file.'.format(path),
                                       'error', colorize))
        try:
            if debug_parser:
                convert(path)
            else:
                prefix = colorcode('{} '.format(path), 'info', colorize)
                with Halo(spinner='bouncingBall', enabled = not quiet):
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

def check_network_connection():
    '''Connects somewhere to test if a network is available.'''
    import requests
    try:
        _ = requests.get('http://www.google.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False


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
        print(colorcode(text, flags), flush = True)
    else:
        print(text, flush = True)


def colorcode(text, flags = None, colorize = True):
    (prefix, color, attributes) = color_codes(flags)
    if colorize:
        if attributes and color:
            return colored(text, color, attrs = attributes)
        elif color:
            return colored(text, color)
        elif attributes:
            return colored(text, attrs = attributes)
        else:
            return text
    elif prefix:
        return prefix + ': ' + text
    else:
        return text


def color_codes(flags):
    color  = ''
    prefix = ''
    attrib = []
    if type(flags) is not list:
        flags = [flags]
    if 'error' in flags:
        prefix = 'ERROR'
        color = 'red'
    if 'warning' in flags:
        prefix = 'WARNING'
        color = 'yellow'
    if 'info' in flags:
        color = 'green'
    if 'white' in flags:
        color = 'white'
    if 'blue' in flags:
        color = 'blue'
    if 'grey' in flags:
        color = 'grey'
    if 'cyan' in flags:
        color = 'cyan'
    if 'underline' in flags:
        attrib.append('underline')
    if 'bold' in flags:
        attrib.append('bold')
    if 'reverse' in flags:
        attrib.append('reverse')
    if 'dark' in flags:
        attrib.append('dark')
    return (prefix, color, attrib)


# -----------------------------------------------------------------------------
# Main entry point.
# -----------------------------------------------------------------------------

def cli_main():
    #The argument parser is inferred - it also deals with too few or too many func args
    plac.call(main)

cli_main()


# Please leave the following for Emacs users.
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
