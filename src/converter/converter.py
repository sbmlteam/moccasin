#!/usr/bin/env python
#
# @file    converter.py
# @brief   MATLAB converter
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# This software is part of MOCCASIN, the Model ODE Converter for Creating
# Awesome SBML INteroperability. Visit https://github.com/sbmlteam/moccasin/.
#
# Copyright (C) 2014 jointly by the following organizations:
#     1. California Institute of Technology, Pasadena, CA, USA
#     2. Mount Sinai School of Medicine, New York, NY, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

import glob
import sys
import pdb
import re
import getopt
from pyparsing import ParseException, ParseResults
from libsbml import *

sys.path.append('..')
sys.path.append('../parser')
from matlab import MatlabGrammar


# -----------------------------------------------------------------------------
# Parsing-related stuff.
# -----------------------------------------------------------------------------

def get_function_scope(mparse):
    # If the outermost scope contains no assignments but does contain a single
    # function, it means the whole file is a function definition.  We want to
    # get at the scope object for the parse results of that function.
    #
    # FIXME: still need to make this deal with the case where the file is a
    # script, not a function definition.
    if mparse and mparse.scope:
        scope = mparse.scope
        if len(scope.functions) == 1 and len(scope.assignments) == 0:
            return scope.functions.itervalues().next()
        else:
            return scope
    else:
        return None


# We turn simple assignments in the outer portion of the file into global
# parameters in the SBML model.

def get_all_assignments(mparse):
    scope = get_function_scope(mparse)
    if not scope:
        return None

    # Loop through the variables and create a dictionary to return.
    parameters = {}
    for id, value in scope.assignments.items():
        # If the variable is an array, we split it by rows.
        if len(value[0]) > 1:
            i = 1
            for row in value[0]:
                new_id = id + "_" + str(i)
                parameters[new_id] = translate_formula(row)
                i += 1
        else:
            parameters[id] = translate_formula(value)
    return parameters


def get_all_function_calls(mparse):
    scope = get_function_scope(mparse)
    if not scope:
        return {}

    calls = {}
    for fname, arglist in scope.calls.items():
        calls[fname] = arglist

    for fname, fscope in scope.functions.items():
        calls.update(get_all_function_calls(fscope.parse_results))
    return calls


def name_is_structured(name):
    return ('[' in name or '(' in name or '{' in name)


def name_mentioned_in_rhs(name, mparse):
    for item in mparse:
        if len(item) > 1:
            # It's an expression.  Look inside each piece recursively.
            if name_mentioned_in_rhs(name, item):
                return True
            else:
                continue
        if len(item) == 1:
            if 'matrix or function' in item:
                item = item['matrix or function']
                if name_mentioned_in_rhs(name, item['argument list']):
                    return True
            elif 'identifier' in item:
                if name == item['identifier']:
                    return True
    return False


def get_lhs_for_rhs(name, mparse):
    scope = get_function_scope(mparse)
    if not scope:
        return None
    for lhs, rhs in scope.assignments.items():
        if name_mentioned_in_rhs(name, rhs):
            return lhs
    return None


def get_function_declaration(name, mparse):
    scope = get_function_scope(mparse)
    if scope and name in scope.functions:
        return scope.functions[name]
    return None


def terminal_value(pr):
    if 'identifier' in pr:
        return pr['identifier']
    elif 'number' in pr:
        return float(pr['number'])
    return None


def row_vector(matrix):
    return len(matrix['row list']) == 1 \
        and len(matrix['row list'][0]['index list']) >= 1


def initial_cond_matrix_size(matrix):
    # Apparently it doesn't matter if the initial conditions matrix passed to
    # ode45 is a row or column vector.  So this checks for either case.
    if row_vector(matrix):
        return len(matrix['row list'][0]['index list'])
    else:
        return len(matrix['row list'])


# -----------------------------------------------------------------------------
# SBML-specific stuff.
# -----------------------------------------------------------------------------

def check(value, message):
    """If 'value' is None, prints an error message constructed using
    'message' and then exits with status code 1.  If 'value' is an integer,
    it assumes it is a libSBML return status code.  If the code value is
    LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
    prints an error message constructed using 'message' along with text from
    libSBML explaining the meaning of the code, and exits with status code 1.
    """
    if value is None:
        print('LibSBML returned a null value trying to ' + message + '.')
        print('Exiting.')
        sys.exit(1)
    elif type(value) is int:
        if value == LIBSBML_OPERATION_SUCCESS:
            return
        else:
            print('Error encountered trying to ' + message + '.')
            print('LibSBML returned error code ' + str(value) + ': "'
                  + OperationReturnValue_toString(value).strip() + '"')
            print('Exiting.')
            sys.exit(1)
    else:
        return


def create_sbml_document():
    # Create model structure
    try:
        return SBMLDocument(3, 1)
    except ValueError:
        print('Could not create SBMLDocumention object')
        sys.exit(1)


def create_sbml_model(document):
    model = document.createModel()
    check(model, 'create model')
    return model


def create_sbml_compartment(model, id, size):
    c = model.createCompartment()
    check(c,                         'create compartment')
    check(c.setId(id),               'set compartment id')
    check(c.setConstant(True),       'set compartment "constant"')
    check(c.setSize(size),           'set compartment "size"')
    check(c.setSpatialDimensions(3), 'set compartment dimensions')
    return c


def create_sbml_species(model, id, value):
    comp = model.getCompartment(0)
    s = model.createSpecies()
    check(s,                                 'create species')
    check(s.setId(id),                       'set species id')
    check(s.setCompartment(comp.getId()),    'set species compartment')
    check(s.setConstant(False),              'set species "constant"')
    check(s.setInitialConcentration(value),  'set species initial concentration')
    check(s.setBoundaryCondition(False),     'set species "boundaryCondition"')
    check(s.setHasOnlySubstanceUnits(False), 'set species "hasOnlySubstanceUnits"')
    return s


def create_sbml_parameter(model, id, value):
    p = model.createParameter()
    check(p,                   'create parameter')
    check(p.setId(id),         'set parameter id')
    check(p.setConstant(True), 'set parameter "constant"')
    check(p.setValue(value),   'set parameter value')
    return p


def create_sbml_initial_assignment(model, id, ast):
    ia = model.createInitialAssignment()
    check(ia,               'create initial assignment')
    check(ia.setMath(ast),  'set initial assignment formula')
    check(ia.setSymbol(id), 'set initial assignment symbol')
    return ia


def create_sbml_raterule(model, id, ast):
    rr = model.createRateRule()
    check(rr,                  'create raterule')
    check(rr.setVariable(id),  'set raterule variable')
    check(rr.setMath(ast),     'set raterule formula')
    return rr


# -----------------------------------------------------------------------------
# Translation code.
# -----------------------------------------------------------------------------
#
# Principles for the SBML "RateRule"-based version of the converter
# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
#
# Matlab's ode* functions handle the following general problem:
#
#     Given a set of differential equations (with X denoting a vector),
#         dX/dt = f(t, X)
#     with initial values X(t_0) = xinit,
#     find the values of the variables X at different times t.
#
# The function defining the differential equations is given as "f" in a call
# to an ode* function such as ode45.  We assume the user provides a Matlab
# file such as the following (and here, the specific formula in the function
# "f" is just an example -- our code does not depend on the details of the
# function, and this is merely a realistic example from a real use case):
#
#     tspan  = [0 300];
#     xinit  = [0; 0];
#     a      = 0.01 * 60;
#     b      = 0.0058 * 60;
#     c      = 0.006 * 60;
#     d      = 0.000192 * 60;
#
#     [t, x] = ode45(@f, tspan, xinit);
#
#     function dx = f(t, x)
#       dx = [a - b * x(1); c * x(1) - d * x(2)];
#     end
#
# In the above, the function "f" passed to Matlab's ode45 is the function "f"
# in the general problem statement.  The body of "f" defines a vector of
# formulas for dx/dt for each variable x. The values of x at different times
# t is what the ode45 function computes.
#
# In create_raterule_model() below, we translate this directly into an SBML
# format that uses "rate rules" to directly encode the dx/dt expressions.
# This uses the name of the variable in the LHS matrix used in the assignment
# of the call to ode45 as the name of the independent variable.  So in other
# words, in the sample above, "x" will be the basis of the species or parameter
# names and the rate rules generated because that's what is used in [t, x] =...

def create_raterule_model(mparse, use_species=False):
    # This assumes there's only one call to an ode* function in the file.  We
    # start by finding that call (wherever it is -- whether it's at the top
    # level, or inside some other function), then inspecting the call, and
    # saving the name of the function handle passed to it as an argument.  We
    # also save the name of the 3rd argument (a vector of initial conditions).

    # Quick summary of pieces we'll gather.  Assume a file like this:
    #   xzero = [num1 num2 ...]                 --> "xzero" is initial_cond_var
    #   [t, y] = ode45(@odefunc, tspan, xzero)  --> "y" is assigned_var
    #   function dy = odefunc(t, x)             --> "x" is dependent_var
    #       dy = [row1; row2; ...]              --> "dy" is output_var
    #   end                                     --> "odefunc" is handle_name

    ode_function = None
    call_arglist = None
    calls = get_all_function_calls(mparse)
    for name, arglist in calls.items():
        if isinstance(name, str) and name.startswith('ode'):
            # Found the invocation of an ode function.
            call_arglist = arglist
            ode_function = name
            break

    if not ode_function:
        fail('Could not locate a call to a Matlab function in the file.')

    # Identify the variables to which the output of the ode call is assigned.
    # It'll be a matrix of the form [t, y].  We want the name of the 2nd
    # variable.  Since it has to be a name, we can extract it using a regexp.
    # This will be the name of the independent variable for the ODE's.
    call_lhs = get_lhs_for_rhs(ode_function, mparse)
    assigned_var = re.sub(r'\[[^\]]+,([^\]]+)\]', r'\1', call_lhs)

    # Matlab ode functions take a handle as 1st arg & initial cond. var as 3rd.
    # FIXME: handle case where function handle is an anonymous function.
    if 'function handle' in call_arglist[0]:
        handle_name = call_arglist[0]['function handle']['name']['identifier']
        initial_cond_var = call_arglist[2]['identifier']

    if not handle_name:
        fail('Could not extract the function handle in the {} call'.format(ode_function))

    # Now locate our scope object for the function definition.  It'll be
    # defined either at the top level (if this file is a script) or inside
    # the scope of the file's overall function (if the file is a function).
    function_scope = get_function_declaration(handle_name, mparse)

    # The function form will have to be f(t, y), because that's what Matlab
    # requires.  We want to find out the name of the parameter 'y' in the
    # actual definition, so that we can locate this variable inside the
    # formula within the function.  We don't know what the user will call it,
    # so we have to use the position of the argument in the function def.
    dependent_var = function_scope.args[1]

    # Find the assignment to the initial condition variable.  The value will
    # be a matrix.  Among other things, we want to find its length, because
    # that tells us the expected length of the output vector, and thus the
    # number of SBML parameters we have to create.
    working_scope = get_function_scope(mparse)
    initial_cond = working_scope.assignments[initial_cond_var]
    if 'matrix' not in initial_cond.keys():
        fail('Failed to parse the assignment of the initial value matrix')
    output_size = initial_cond_matrix_size(initial_cond['matrix'])

    # If we get this far, let's start generating some SBML.

    document = create_sbml_document()
    model = create_sbml_model(document)
    compartment = create_sbml_compartment(model, 'comp1', 1)

    # Create either parameters or species (depending on the run-time selection)
    # for the dependent variables and set their initial values.
    is_row_vector = row_vector(initial_cond['matrix'])
    for i in range(0, output_size):
        if is_row_vector:
            the_value = terminal_value(initial_cond['matrix'][0]['index list'][i])
        else:
            the_value = terminal_value(initial_cond['matrix'][i]['index list'][0])
        the_name = assigned_var + '_' + str(i + 1)
        # FIXME assumes the_value is a number, but it could be a variable, in
        # which case we should look up that variable's value elsewhere.
        if use_species:
            create_sbml_species(model, the_name, the_value)
        else:
            p = create_sbml_parameter(model, the_name, the_value)
            p.setConstant(False)

    # Now, look inside the function definition and find the assignment to the
    # function's output variable. (It corresponds to assigned_var, but inside
    # the function.)  This defines the formula for the ODE.  We expect this
    # to be a vector.  We take it apart, using each row as an ODE definition,
    # and use this to create SBML "rate rules" for the output variables.
    output_var = function_scope.returns[0]
    var_def = function_scope.assignments[output_var]
    if 'matrix' not in var_def:
        fail('Failed to parse the body of the function {}'.format(handle_name))
    matrix = var_def['matrix']
    i = 1
    for row in matrix['row list']:
        # Currently, this assumes there's only one math expression per row,
        # meaning, one index value per row, so we index [0] directly.  FIXME.
        if 'index list' not in row:
            fail('Failed to parse the matrix assigned to {}'.format(output_def))
        parsed_formula = row['index list'][0]
        string_formula = MatlabGrammar.make_formula(parsed_formula)
        if not string_formula:
            fail('Failed to parse the formula for row {}'.format(i))

        # We need to rewrite matrix references "x(n)" to the form "x_n", and
        # rename the variable to the name used for the results assignment
        # in the call to the ode* function.
        xnameregexp = dependent_var + r'\((\d+)\)'
        newnametranform = assigned_var + r'_\1'
        formula = re.sub(xnameregexp, newnametranform, string_formula)

        # Finally, write the rate rule.
        rule_var = assigned_var + "_" + str(i)
        ast = parseL3Formula(formula)
        create_sbml_raterule(model, rule_var, ast)
        i += 1

    # Create remaining parameters.  Here, we have to decide what to do about
    # possible duplicate variable names showing up inside the function and
    # outside.  The approach here is to have the ones inside the function
    # shadow the ones outside, but we should really check if something more
    # complicated is going on in the Matlab code.
    # FIXME doesn't handle matrices on the LHS.

    for var, rhs in dict(working_scope.assignments.items()
                         + function_scope.assignments.items()).items():
        if not name_is_structured(var):
            if 'number' in rhs:
                create_sbml_parameter(model, var, terminal_value(rhs))
            elif 'matrix' not in rhs:
                create_sbml_parameter(model, var, 0)
                formula = MatlabGrammar.make_formula(rhs)
                ast = parseL3Formula(formula)
                if ast is not None:
                    create_sbml_initial_assignment(model, var, ast)

    # Write the Model
    return writeSBMLToString(document)


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

def get_filename_and_options(argv):
    try:
        options, path = getopt.getopt(argv[1:], "dpqs")
    except:
        raise SystemExit(main.__doc__)
    if len(path) != 1 or len(options) > 2:
        raise SystemExit(main.__doc__)
    debug       = any(['-d' in y for y in options])
    do_print    = any(['-p' in y for y in options])
    quiet       = any(['-q' in y for y in options])
    use_species = any(['-s' in y for y in options])
    return path[0], debug, quiet, do_print, use_species


def main(argv):
    '''Usage: converter.py [-d] [-p] [-q] [-s] FILENAME.m
Arguments:
 -d  (Optional) Drop into pdb before starting to parse the MATLAB input
 -p  (Optional) Print a debugging representation of the interpreted MATLAB
 -q  (Optional) Be quiet; just produce SBML, nothing else
 -s  (Optional) Turn variables into species (default: make them parameters)
'''
    path, debug, quiet, print_parse, use_species = get_filename_and_options(argv)

    file = open(path, 'r')
    file_contents = file.read()
    file.close()

    if not quiet:
        print('----- file ' + path + ' ' + '-'*30)
        print(file_contents)

    if debug:
        pdb.set_trace()

    try:
        parser = MatlabGrammar()
        parse_results = parser.parse_string(file_contents)
    except ParseException as err:
        print("error: {0}".format(err))

    if print_parse and not quiet:
        print('')
        print('----- interpreted output ' + '-'*50)
        parser.print_parse_results(parse_results)

    if not quiet:
        print('')
        print('----- SBML output ' + '-'*50)

    sbml = create_raterule_model(parse_results, use_species)
    print sbml


def fail(msg):
    raise SystemExit(msg)


if __name__ == '__main__':
    main(sys.argv)
