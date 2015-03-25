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
# Copyright (C) 2014-2015 jointly by the following organizations:
#  1. California Institute of Technology, Pasadena, CA, USA
#  2. Mount Sinai School of Medicine, New York, NY, USA
#  3. Boston University, Boston, MA, USA
#
# This is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation.  A copy of the license agreement is provided in the
# file named "COPYING.txt" included with this software distribution and also
# available online at https://github.com/sbmlteam/moccasin/.
# ------------------------------------------------------------------------- -->

from __future__ import print_function
import glob
import sys
import pdb
import re
import getopt
import six
import itertools
from pyparsing import ParseException, ParseResults
from evaluate_formula import NumericStringParser
from libsbml import *

sys.path.append('..')
from matlab_parser import *


# -----------------------------------------------------------------------------
# Globals.
# -----------------------------------------------------------------------------

anon_counter = 0
need_time = False


# -----------------------------------------------------------------------------
# Parsing-related stuff.
# -----------------------------------------------------------------------------

def get_function_context(context):
    # If the outermost context contains no assignments but does contain a single
    # function, it means the whole file is a function definition.  We want to
    # get at the context object for the parse results of that function.
    if context:
        if len(context.functions) == 1 and len(context.assignments) == 0:
            return six.next(six.itervalues(context.functions))
        else:
            return context
    else:
        return None


def get_assignment(name, context):
    if name in context.assignments:
        return context.assignments[name]
    elif hasattr(context, 'parent') and context.parent:
        return get_assignment(name, context.parent)
    else:
        return None


def get_all_assignments(context):
    # Loop through the variables and create a dictionary to return.
    assignments = {}
    for var, rhs in context.assignments.items():
        assignments[var] = rhs
    for fname, fcontext in context.functions.items():
        assignments.update(get_all_assignments(fcontext))
    return assignments


def get_all_function_calls(context):
    calls = {}
    for fname, arglist in context.calls.items():
        calls[fname] = arglist
    for fname, fcontext in context.functions.items():
        calls.update(get_all_function_calls(fcontext))
    return calls


def name_is_structured(name):
    return ('[' in name or '(' in name or '{' in name)


def name_mentioned_in_rhs(name, node):
    if isinstance(node, ArrayOrFunCall) or isinstance(node, FunCall):
        if isinstance(node.name, Identifier) and name == node.name.name:
            return True
        if name_mentioned_in_rhs(name, node.args):
            return True
    elif isinstance(node, Identifier):
        if name == node.name:
            return True

    search_list = []
    if isinstance(node, list):
        search_list = node
    elif isinstance(node, Expression):
        search_list = node.content
    for term in search_list:
        if name_mentioned_in_rhs(name, term):
            return True

    return False


def get_lhs_for_rhs(name, context):
    for lhs, rhs in context.assignments.items():
        if name_mentioned_in_rhs(name, rhs):
            return lhs
    return None


def get_assignment_rule(name, context):
    for lhs, rhs in context.assignments.items():
        if lhs == name:
            return rhs
    return None


def get_function_declaration(name, context):
    if context and name in context.functions:
        return context.functions[name]
    return None


def is_row_vector(matrix):
    return (len(matrix.rows) == 1 and len(matrix.rows[0]) >= 1)


def vector_length(matrix):
    if is_row_vector(matrix):
        return len(matrix.rows[0])
    else:
        return len(matrix.rows)


def mloop(matrix, func):
    # Calls function 'func' on a row or column of values from the matrix.
    # Note: the argument 'i' is 0-based, not 1-based like Matlab vectors.
    # FIXME: this only handles 1-D row or column vectors.
    row_vector = is_row_vector(matrix)
    row_length = vector_length(matrix)
    base = matrix.rows
    for i in range(0, row_length):
        if row_vector:
            entry = base[0][i]
        else:
            entry = base[i][0]
        func(i, entry)


def inferred_type(name, context, recursive=False):
    if isinstance(name, Identifier):
        name = name.name
    if name in context.types:
        return context.types[name]
    elif recursive and hasattr(context, 'parent') and context.parent:
        return inferred_type(name, context.parent, True)
    else:
        return None


def num_underscores(context):
    # Look if any variables use underscores in their name.  Count the longest
    # sequence of underscores found.  Recursively looks in subcontexts too.
    longest = 0
    for name in context.assignments:
        if '_' in name:
            this_longest = len(max(re.findall('(_+)', name), key=len))
            longest = max(longest, this_longest)
    if context.functions:
        for subcontext in six.itervalues(context.functions):
            longest = max(num_underscores(subcontext), longest)
    return longest


def rename(base, tail='', num_underscores=1):
    return ''.join([base, '_'*num_underscores, tail])


def parse_handle(thing, context, underscores):
    # Cases:
    #  @foo => foo is the function name
    #  @(args)body => cases:
    #   - body is a variable that holds another function handle => chase it
    #   - body is a function call => return the function name
    #   - body is a matrix
    if isinstance(thing, FunHandle):
        # Case: ode45(@foo, time, xinit, ...)
        # The item has to be an identifier -- MATLAB won't allow anything else.
        return thing.name.name
    elif isinstance(thing, Identifier):
        # Case: ode45(somevar, trange, xinit, ...)
        # Look up the value of somevar and see if that's a function handle.
        if thing.name in context.assignments:
            value = context.assignments[thing.name]
            if isinstance(value, FunHandle):
                # The name of the handle must be an identifier, so dereference it.
                return value.name.name
            elif isinstance(value, AnonFun):
                # Reset thing to the body and fall through to the AnonFun case.
                thing = value
            else:
                # Variable value is not a function handle.
                return None
        else:
            # Looks like a variable, but we don't know its value.
            fail('{} is unknown'.format(thing.name))

    # This next thing is not an else-if because may get here two different ways.
    if isinstance(thing, AnonFun):
        # Case: ode45(@(args)..., time, xinit)
        if isinstance(thing.body, ArrayOrFunCall) or isinstance(thing.body, FunCall):
            # Body is just a function call.
            if isinstance(thing.body.name, Identifier):
                # The name is a plain identifier -- good.
                return thing.body.name.name
            else:
                # The function name is not an identifier but more complicated,
                # perhaps a struct.  Currently, we can't deal with it.
                return None
        elif isinstance(thing.body, Array):
            # Body is an array.  In our domain of ODE and similar models, it
            # means it's the equivalent of a function body.  Approach: create
            # a new fake function, store it, and return its name.
            name = create_array_function(thing, context, underscores)
            return name
    else:
        return None


def create_array_function(thing, context, underscores):
    if not isinstance(thing, AnonFun):
        # Shouldn't be here in the first place.
        return None
    args = thing.args
    func_name = new_anon_name()
    output_var_name = func_name + '_'*underscores + 'out'
    output_var = Identifier(name=output_var_name)
    newcontext = MatlabContext(func_name, context, None, args, [output_var])
    newcontext.assignments[output_var_name] = thing.body
    newcontext.types[output_var_name] = 'variable'
    for var in args:
        newcontext.types[var.name] = 'variable'
    context.functions[func_name] = newcontext
    return func_name


def new_anon_name():
    global anon_counter
    anon_counter += 1
    return 'anon{:03d}'.format(anon_counter)


def substitute_vars(rhs, context):
    result = []
    for item in rhs:
        if isinstance(item, Identifier):
            assigned_value = get_assignment(item.name, context)
            if assigned_value:
                result.append(assigned_value)
                continue
        elif isinstance(item, list):
            subresult = []
            for subitem in item:
                subresult.append(subitem)
            result.append(substitute_vars(subresult, context))
            continue
        result.append(item)
    return result


# -----------------------------------------------------------------------------
# XPP specific stuff
# -----------------------------------------------------------------------------

def create_xpp_parameter(xpp_variables, id, value, constant=True,
                         rate_rule='', init_assign=''):
    parameter = dict({'SBML_type': 'Parameter',
                      'id': id,
                      'value': float(value),
                      'constant': constant,
                      'init_assign': init_assign,
                      'rate_rule': rate_rule})
    xpp_variables.append(parameter)
    return xpp_variables


def create_xpp_species(xpp_variables, id, value, rate_rule='', init_assign=''):
    species = dict({'SBML_type': 'Species',
                    'id': id,
                    'value': float(value),
                    'constant': False,
                    'init_assign': init_assign,
                    'rate_rule': rate_rule})
    xpp_variables.append(species)
    return xpp_variables


def add_xpp_raterule(model, id, ast):
    for i in range(0, len(model)):
        if model[i]['id'] == id:
            model[i]['rate_rule'] = ast
            break
    return


def make_xpp_indexed(var, index, content, species, model, underscores, context):
    name = rename(var, str(index + 1), underscores)
    if isinstance(content, Number):
        if species:
            model = create_xpp_species(model, name, content.value)
        else:
            model = create_xpp_parameter(model, name, content.value, False)
    else:
        translator = lambda node: munge_reference(node, context, underscores)
        formula = MatlabGrammar.make_formula(content, atrans=translator)
        if species:
            model = create_xpp_species(model, name, 0, formula)
        else:
            model = create_xpp_parameter(model, name, 0, False, formula)


def make_xpp_raterule(assigned_var, dep_var, index, content, model, underscores, context):
    # Currently, this assumes there's only one math expression per row or
    # column, meaning, one subscript value per row or column.

    translator = lambda node: munge_reference(node, context, underscores)
    string_formula = MatlabGrammar.make_formula(content, atrans=translator)
    if not string_formula:
        fail('Failed to parse the formula for row {}'.format(index + 1))

    # We need to rewrite matrix references "x(n)" to the form "x_n", and
    # rename the variable to the name used for the results assignment
    # in the call to the ode* function.
    xnameregexp = dep_var + '_'*underscores + r'(\d+)'
    newnametransform = assigned_var + '_'*underscores + r'\1'
    formula = re.sub(xnameregexp, newnametransform, string_formula)

    # Finally, write the rate rule.
    rule_var = assigned_var + '_'*underscores + str(index + 1)
    add_xpp_raterule(model, rule_var, formula)


def create_xpp_string(xpp_elements):
    # create the lines of the file that will be the output
    lines = '#\n# This file is generated by MOCCASIN\n#\n\n'

    num_objects = len(xpp_elements)

    # output constant parameters
    for i in range(0, num_objects):
        element = xpp_elements[i]
        if element['SBML_type'] == 'Parameter':
            if element['constant'] is True:
                id = element['id']
                value = element['value']
                lines += ('# Parameter id = {}, constant\n'.format(id))
                # this does not seem to work
                # FIX ME
                if element['init_assign'] != '':
                    lines += ('par {}={}\n\n'.format(id, element['init_assign']))
                else:
                    lines += ('par {}={}\n\n'.format(id, value))
            elif element['rate_rule'] == '':
                id = element['id']
                value = element['value']
                lines += ('# Parameter id = {}, '
                          'non-constant but no rule supplied\n'.format(id))
                lines += ('par {}={}\n\n'.format(id, value))

    # output odes
    for i in range(0, num_objects):
        element = xpp_elements[i]
        if element['SBML_type'] == 'Parameter':
            if element['constant'] is False and element['rate_rule'] != '':
                id = element['id']
                value = element['value']
                formula = element['rate_rule']
                lines += ('# rateRule : variable = {}\n'.format(id))
                lines += ('init {}={}\n'.format(id, value))
                lines +=('d{}/dt={}\n\n'.format(id, formula))
        elif element['SBML_type'] == 'Species':
            id = element['id']
            value = element['value']
            formula = element['rate_rule']
            lines += ('# rateRule : variable = {}\n'.format(id))
            lines += ('init {}={}\n'.format(id, value))
            lines +=('d{}/dt={}\n\n'.format(id, formula))

    #output the sbml equivalent of variables
    for i in range(0, num_objects):
        element = xpp_elements[i]
        if element['SBML_type'] == 'Parameter':
            if element['constant'] is False and element['rate_rule'] != '':
                id = element['id']
                sbml = element['SBML_type']
                lines += ('# {}:   id = {}, defined by rule\n\n'
                          .format(sbml, id))
        elif element['SBML_type'] == 'Species':
            id = element['id']
            sbml = element['SBML_type']
            lines += ('# {}:   id = {}, defined by rule\n\n'.format(sbml, id))

    lines += 'done\n'

    return lines



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


def create_sbml_compartment(model, id, size, const=True):
    c = model.createCompartment()
    check(c,                         'create compartment')
    check(c.setId(id),               'set compartment id')
    check(c.setConstant(const),      'set compartment "constant"')
    check(c.setSize(float(size)),    'set compartment "size"')
    check(c.setSpatialDimensions(3), 'set compartment dimensions')
    return c


def create_sbml_species(model, id, value, const=False):
    comp = model.getCompartment(0)
    s = model.createSpecies()
    check(s,                                       'create species')
    check(s.setId(id),                             'set species id')
    check(s.setCompartment(comp.getId()),          'set species compartment')
    check(s.setConstant(const),                    'set species "constant"')
    check(s.setInitialConcentration(float(value)), 'set species initial concentration')
    check(s.setBoundaryCondition(False),           'set species "boundaryCondition"')
    check(s.setHasOnlySubstanceUnits(False),       'set species "hasOnlySubstanceUnits"')
    return s


def create_sbml_parameter(model, id, value, const=True):
    p = model.createParameter()
    check(p,                        'create parameter')
    check(p.setId(id),              'set parameter id')
    check(p.setConstant(const),     'set parameter "constant"')
    check(p.setValue(float(value)), 'set parameter value')
    return p


def create_sbml_initial_assignment(model, id, ast):
    ia = model.createInitialAssignment()
    check(ia,               'create initial assignment')
    check(ia.setMath(ast),  'set initial assignment formula')
    check(ia.setSymbol(id), 'set initial assignment symbol')
    return ia


def create_sbml_raterule(model, id, ast):
    rr = model.createRateRule()
    check(rr,                  'create rate rule')
    check(rr.setVariable(id),  'set rate rule variable')
    check(rr.setMath(ast),     'set rate rule formula')
    return rr


def create_sbml_assignment_rule(model, id, ast):
    rr = model.createAssignmentRule()
    check(rr,                  'create assignment rule')
    check(rr.setVariable(id),  'set assignment rule variable')
    check(rr.setMath(ast),     'set assignment rule formula')
    return rr


def make_indexed(var, index, content, species, model, underscores, context):
    # Helper function:
    def create_species_or_parameter(the_name, the_value):
        if species:
            item = create_sbml_species(model, the_name, the_value, const=False)
        else:
            item = create_sbml_parameter(model, the_name, the_value, const=False)

    name = rename(var, str(index + 1), underscores)
    if isinstance(content, Number):
        create_species_or_parameter(name, content.value)
        return
    elif isinstance(content, Identifier):
        # Check if we have the simple case of a variable whose value is
        # *another* variable whose value in turn is a number.
        assigned_value = get_assignment(name, context)
        if assigned_value and isinstance(assigned_value, Number):
            create_species_or_parameter(name, assigned_value.value)
            return

    # Fall-back case: create an initial assignment.
    if species:
        item = create_sbml_species(model, name, 0, const=False)
    else:
        item = create_sbml_parameter(model, name, 0, const=False)
    translator = lambda node: munge_reference(node, context, underscores)
    formula = MatlabGrammar.make_formula(content, atrans=translator)
    ast = parseL3Formula(formula)
    create_sbml_initial_assignment(model, name, ast)


def make_raterule(assigned_var, dep_var, index, content, model, underscores, context):
    # Currently, this assumes there's only one math expression per row or
    # column, meaning, one subscript value per row or column.

    translator = lambda node: munge_reference(node, context, underscores)
    string_formula = MatlabGrammar.make_formula(content, atrans=translator)
    if not string_formula:
        fail('Failed to parse the formula for row {}'.format(index + 1))

    # We need to rewrite matrix references "x(n)" to the form "x_n", and
    # rename the variable to the name used for the results assignment
    # in the call to the ode* function.
    xnameregexp = dep_var + '_'*underscores + r'(\d+)'
    newnametransform = assigned_var + '_'*underscores + r'\1'
    formula = re.sub(xnameregexp, newnametransform, string_formula)

    # Finally, write the rate rule.
    rule_var = assigned_var + '_'*underscores + str(index + 1)
    ast = parseL3Formula(formula)
    create_sbml_raterule(model, rule_var, ast)


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
# In create_raterule_model() below, we translate this directly into
# either
#
# 1. an SBML format that uses "rate rules" to directly encode the dx/dt
# expressions.
# This uses the name of the variable in the LHS matrix used in the assignment
# of the call to ode45 as the name of the independent variable.  So in other
# words, in the sample above, "x" will be the basis of the species or parameter
# names and the rate rules generated because that's what is used in [t, x] =...
#
# or
# 2. an XPP format that captures the parameters and odes

def create_raterule_model(parse_results, use_species=True, produce_sbml=True):
    # This assumes there's only one call to an ode* function in the file.  We
    # start by finding that call (wherever it is -- whether it's at the top
    # level, or inside some other function), then inspecting the call, and
    # saving the name of the function handle passed to it as an argument.  We
    # also save the name of the 3rd argument (a vector of initial conditions).

    # Gather some preliminary info.
    working_context = get_function_context(parse_results)
    underscores = num_underscores(working_context) + 1

    # Look for a call to a MATLAB ode* function.
    ode_function = None
    call_arglist = None
    calls = get_all_function_calls(working_context)
    for name, arglist in calls.items():
        if isinstance(name, str) and re.match('^ode[0-9]', name):
            # Found the invocation of an ode function.
            call_arglist = arglist
            ode_function = name
            break

    if not ode_function:
        fail('Could not locate a call to a Matlab function in the file.')

    # Quick summary of pieces we'll gather.  Assume a file like this:
    #   xzero = [num1 num2 ...]                 --> "xzero" is init_cond_var
    #   [t, y] = ode45(@odefunc, tspan, xzero)  --> "y" is assigned_var
    #   function dy = odefunc(t, x)             --> "x" is dependent_var
    #       dy = [row1; row2; ...]              --> "dy" is output_var
    #   end                                     --> "odefunc" is handle_name

    # Identify the variables to which the output of the ode call is assigned.
    # It'll be a matrix of the form [t, y].  We want the name of the 2nd
    # variable.  Since it has to be a name, we can extract it using a regexp.
    # This will be the name of the independent variable for the ODE's.
    call_lhs = get_lhs_for_rhs(ode_function, working_context)
    assigned_var = re.sub(r'\[[^\]]+,([^\]]+)\]', r'\1', call_lhs)

    # Matlab ode functions take a handle as 1st arg & initial cond. var as 3rd.
    init_cond_var = call_arglist[2]
    if isinstance(init_cond_var, Identifier):
        init_cond_var = init_cond_var.name
    else:
        fail('Unable to extract initial conditions variable in call to ODE function {}'
             .format(ode_function))
    handle_name = parse_handle(call_arglist[0], working_context, underscores)
    if not handle_name:
        fail('Could not determine ODE function from call to {}'
             .format(ode_function))

    # If we get this far, let's start generating some code.

    if produce_sbml:
        document = create_sbml_document()
        model = create_sbml_model(document)
        compartment = create_sbml_compartment(model, 'comp1', 1)
    else:
        xpp_variables = []

    # Now locate our context object for the function definition.  It'll be
    # defined either at the top level (if this file is a script) or inside
    # the context of the file's overall function (if the file is a function).
    function_context = get_function_declaration(handle_name, working_context)
    if not function_context:
        fail('Cannot locate definition for function {}'.format(handle_name))

    # The function form will have to be f(t, y), because that's what Matlab
    # requires.  We want to find out the name of the parameter 'y' in the
    # actual definition, so that we can locate this variable inside the
    # formula within the function.  We don't know what the user will call it,
    # so we have to use the position of the argument in the function def.
    dependent_var = function_context.parameters[1]
    if isinstance(dependent_var, Identifier):
        dependent_var = dependent_var.name
    else:
        fail('Failed to parse the arguments to function {}.'.format(handle_name))

    # Find the assignment to the initial condition variable, then create
    # either parameters or species (depending on the run-time selection) for
    # each entry.  The initial value of the parameter/species will be the
    # value in the matrix.
    init_cond = working_context.assignments[init_cond_var]
    if not isinstance(init_cond, Array):
        fail('Failed to parse the assignment of the initial value matrix')

    if produce_sbml:
        mloop(init_cond,
              lambda idx, item: make_indexed(assigned_var, idx, item,
                                             use_species, model, underscores,
                                             function_context))
    else:
        mloop(init_cond,
              lambda idx, item: make_xpp_indexed(assigned_var, idx, item,
                                                 use_species, xpp_variables,
                                                 underscores, function_context))

    # Now, look inside the function definition and find the assignment to the
    # function's output variable. (It corresponds to assigned_var, but inside
    # the function.)  This defines the formula for the ODE.  We expect this
    # to be a vector.  We take it apart, using each row as an ODE definition,
    # and use this to create SBML "rate rules" for the output variables.
    #
    # Tricky case: the file may mix assignments to the output variable as a
    # single name with assignments to individual elements of an array.  E.g.:
    #
    #    function y = foo(t,x)
    #    y = zeros(4,1);
    #     ...
    #    y(1) = ... something
    #    y(2) = ... something
    #    ... etc.
    #
    # Our problem then is to match up the variables.  We do this by rewriting
    # the assignments in the call to reconstruct_separate_assignments().

    output_var = function_context.returns[0].name
    reconstruct_separate_assignments(function_context, output_var, underscores)
    var_def = function_context.assignments[output_var]
    if not isinstance(var_def, Array):
        fail('Failed to parse the body of the function {}'.format(handle_name))

    if produce_sbml:
        mloop(var_def,
              lambda idx, item: make_raterule(assigned_var, dependent_var,
                                              idx, item, model, underscores,
                                              function_context))
    else:
        mloop(var_def,
              lambda idx, item: make_xpp_raterule(assigned_var, dependent_var,
                                                  idx, item, xpp_variables,
                                                  underscores, function_context))

    # Create remaining parameters.  This breaks up matrix assignments by
    # looking up the value assigned to the variable; if it's a matrix value,
    # then the variable is turned into parameters named foo_1, foo_2, etc.
    # Also, we have to decide what to do about duplicate variable names
    # showing up inside the function body and outside.  The approach here is
    # to have variables inside the function shadow ones outside, but we
    # should really check if something more complicated is going on in the
    # Matlab code.  The shadowing is done by virtue of the fact that the
    # creation of the dict() object for the next for-loop uses the sum of
    # the working context and function context dictionaries, with the function
    # context taken second (which means its values are the final ones).

    skip_vars = [init_cond_var, output_var, assigned_var]
    if isinstance(call_arglist[1], Identifier):
        # Sometimes people use an array for the time parameter.  In that case,
        # it doesn't matter for what happens below.  But if it's a named
        # variable, we want to skip it.
        skip_vars.append(call_arglist[1].name)

    all_vars = dict(itertools.chain(working_context.assignments.items(),
                                    function_context.assignments.items()))
    formula_parser = NumericStringParser()
    translator = lambda node: munge_reference(node, function_context,
                                                      underscores)
    for var, rhs in all_vars.items():
        if var in skip_vars:
            continue
        # FIXME currently doesn't handle matrices on LHS.
        if name_is_structured(var):
            continue
        if isinstance(rhs, Number):
            if produce_sbml:
                create_sbml_parameter(model, var, rhs.value)
            else:
                create_xpp_parameter(xpp_variables, var, rhs.value)
        elif isinstance(rhs, Identifier):
            # Refers to another variable, i.e., something of the form "x = y".
            # Keep it if we can, because it might be preferrable that way.
            # (After all, the user probably wrote x = y for a reason.)
            if produce_sbml:
                ast = parseL3Formula(rhs.name)
                if ast is not None:
                    create_sbml_parameter(model, var, 0)
                    create_sbml_initial_assignment(model, var, ast)
            else:
                # Can't do that in XPP output.  Check if we can subsitute.
                assigned_value = get_assignment(rhs.name, function_context)
                if isinstance(assigned_value, Number):
                    result = assigned_value.value
                else:
                    substituted = substitute_vars(assigned_value, working_context)
                    formula = MatlabGrammar.make_formula(substituted, atrans=translator)
                    if formula:
                        result = formula_parser.eval(formula)
                    else:
                        # Not sure what else to do here.
                        result = rhs.name
                create_xpp_parameter(xpp_variables, var, result)
        elif isinstance(rhs, Array):
            if produce_sbml:
                mloop(rhs,
                      lambda idx, item: make_indexed(var, idx, item, False,
                                                     model, underscores,
                                                     function_context))
            else:
                mloop(rhs,
                      lambda idx, item: make_xpp_indexed(var, idx, item, False,
                                                         xpp_variables,
                                                         underscores,
                                                         function_context))
        elif isinstance(rhs, FunHandle):
            # Skip function handles. If any was used in the ode* call, it will
            # have been dealt with earlier.
            continue
        elif isinstance(rhs, ArrayRef) or isinstance(rhs, list) \
             or isinstance(rhs, FunCall) or isinstance(rhs, Expression):
            # Inefficient way to do this, but for now let's just do this.
            if isinstance(rhs, ArrayRef):   rhs = rhs.args
            if isinstance(rhs, FunCall):
                # we cannot evaluate just any function
                # leaving this here because I'm not sure whether the
                # sbml will need it; but xpp does not deal with it
                # note the sbml ends up with a null ast so exists neatly
                if produce_sbml:
                    rhs = [rhs]
                else:
                    continue
            if isinstance(rhs, Expression): rhs = rhs.content
            if produce_sbml:
                formula = MatlabGrammar.make_formula(rhs, atrans=translator)
                ast = parseL3Formula(formula)
                if ast is not None:
                    create_sbml_parameter(model, var, 0)
                    create_sbml_initial_assignment(model, var, ast)
            else:
                substituted = substitute_vars(rhs, working_context)
                formula = MatlabGrammar.make_formula(substituted, atrans=translator)
                if formula:
                    result = formula_parser.eval(formula)
                    create_xpp_parameter(xpp_variables, var, result)

    # Final quirks.
    if need_time:
        if produce_sbml:
            create_sbml_parameter(model, "t", 0, const=False)
            create_sbml_assignment_rule(model, "t", parseL3Formula("time"))
        else:
            result = formula_parser.eval("t")
            create_xpp_parameter(xpp_variables, var, result)

    # Write the Model
    if produce_sbml:
        return writeSBMLToString(document)
    else:
        return create_xpp_string(xpp_variables)


# FIXME only handles 1-D matrices.
# FIXME grungy part for looking up identifier -- clean up & handle more depth

def munge_reference(array, context, underscores):
    name = array.name.name
    if inferred_type(name, context) != 'variable':
        return MatlabGrammar.make_key(array)
    # Base name starts with one less underscore because the loop process
    # adds one in front of each number.
    constructed = name + '_'*(underscores - 1)
    for i in range(0, len(array.args)):
        element = array.args[i]
        i += 1
        if isinstance(element, Number):
            constructed += '_' + element.value
        elif isinstance(element, Identifier):
            # The subscript is not a number.  If it's a simple variable and
            # we've seen its value, we can handle it by looking up its value.
            assignments = get_all_assignments(context)
            var_name = element.name
            if var_name not in assignments:
                raise ValueError('Unable to handle "' + name + '"')
            assigned_value = assignments[var_name]
            if isinstance(assigned_value, Number):
                constructed += '_' + assigned_value
            else:
                raise ValueError('Unable to handle "' + name + '"')
    return constructed


def reconstruct_separate_assignments(context, var, underscores):
    # Look through the context for assignments to variables having names of
    # the form "x(1)", where "x" is the value of parameter var.  If we find
    # any, we assume they are rows of an array.  We collect them into a real
    # Array object and assign the array as the value of var.  We also delete
    # the original "x(1)" etc. entries.

    need_adjust = []
    for name in context.assignments.keys():
        if name.startswith(var) and name.find('(') > 0:
            need_adjust.append(name)
    if need_adjust:
        # We will build a new array with as many rows as individual elements
        # have been assigned in this context.
        new_value = [None]*len(need_adjust)
        for elem_name in need_adjust:
            elem_index = re.sub(var + r'\((\d+)\)', r'\1', elem_name)
            # The -1 is because Python arrays are 0-indexed
            new_value[int(elem_index) - 1] = [context.assignments[elem_name]]
            context.assignments.pop(elem_name)
        context.assignments[var] = Array(rows=new_value, is_cell=False)


# -----------------------------------------------------------------------------
# MATLAB rewriter
#
# This rewrites some simple MATLAB constructs to something we can deal with.
# -----------------------------------------------------------------------------

def rewrite_recognized_matlab(context):
    for function_name, function_context in context.functions.items():
        for lhs, rhs in function_context.assignments.items():
            function_context.assignments[lhs] = rewrite_known_matlab(rhs)
        for name, args in function_context.calls.items():
            function_context.calls[name] = rewrite_known_matlab(args)
        function_context.nodes = rewrite_known_matlab(function_context.nodes)
        rewrite_recognized_matlab(function_context)


def rewrite_known_matlab(thing):
    if isinstance(thing, list):
        return [rewrite_known_matlab(item) for item in thing]
    elif isinstance(thing, FunCall):
        # Item is a function call.  Is it something we know about?
        if isinstance(thing.name, Identifier):
            func = thing.name.name
            if func in matlab_converters:
                return matlab_converters[func](thing.args)
    elif isinstance(thing, Identifier) and thing.name == "t":
        # Assume this is a reference to time.
        global need_time
        need_time = True
    # Item is none of the above. Leave it untouched.
    return thing


# E.g.: zeros(3,1) produces a matrix
def matlab_zeros(args):
    if len(args) == 1:
        rows = int(args[0].value)
        return Array(rows=[[Number(value='0')]]*rows, is_cell=False)
    elif len(args) == 2:
        rows = int(args[0].value)
        cols = int(args[1].value)
        return Array(rows=[[Number(value='0')]*cols]*rows, is_cell=False)


matlab_converters = {
    'zeros': matlab_zeros
}


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

def get_filename_and_options(argv):
    try:
        options, path = getopt.getopt(argv[1:], "dpqxo")
    except:
        raise SystemExit(main.__doc__)
    if len(path) != 1 or len(options) > 2:
        raise SystemExit(main.__doc__)
    debug       = any(['-d' in y for y in options])
    quiet       = any(['-q' in y for y in options])
    print_parse = any(['-x' in y for y in options])
    use_species = not any(['-p' in y for y in options])
    create_sbml = not any(['-o' in y for y in options])
    return path[0], debug, quiet, print_parse, use_species, create_sbml


def main(argv):
    '''Usage: converter.py [options] FILENAME.m
Available options:
 -d   Drop into pdb before starting to parse the MATLAB input
 -h   Print this help message and quit
 -p   Turn variables into parameters (default: make them species)
 -q   Be quiet; just produce code, nothing else
 -x   Print extra debugging info about the interpreted MATLAB
 -o   Create the XPP conversion (SBML is created by default)
'''
    path, debug, quiet, print_parse, use_species, create_sbml \
        = get_filename_and_options(argv)

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
    except Exception as err:
        print("error: {0}".format(err))

    if print_parse and not quiet:
        print('')
        print('----- interpreted output ' + '-'*50)
        parser.print_parse_results(parse_results)

    if not quiet:
        print('')
        if create_sbml:
            print('----- SBML output ' + '-'*50)
        else:
            print('----- XPP output ' + '-'*50)

    rewrite_recognized_matlab(parse_results)
    code = create_raterule_model(parse_results, use_species, create_sbml)
    print(code)


def fail(msg):
    raise SystemExit(msg)


if __name__ == '__main__':
    main(sys.argv)
