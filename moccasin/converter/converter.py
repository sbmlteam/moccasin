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
from version import __version__


# -----------------------------------------------------------------------------
# Globals.
# -----------------------------------------------------------------------------

GLOBALS = {'need time': False, 'anon counter': 0}

def reset_globals():
    global GLOBALS
    GLOBALS['need time'] = False
    GLOBALS['anon counter'] = 0


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
    global GLOBALS
    GLOBALS['anon counter'] += 1
    return 'anon{:03d}'.format(GLOBALS['anon counter'])


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


# Clever technique found at http://stackoverflow.com/a/1325265/743730
def valid_id(text, search=re.compile(r'\A[a-zA-Z_][a-zA-Z0-9_]*\Z').search):
    return bool(search(text))


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


def add_xpp_raterule(xpp_variables, id, ast):
    for i in range(0, len(xpp_variables)):
        if xpp_variables[i]['id'] == id:
            xpp_variables[i]['rate_rule'] = ast
            break


def create_xpp_assignment(xpp_variables, id, formula, additional_info=[]):
    # hack to make this work by putting in a parameter
    parameter = dict({'SBML_type': 'Parameter',
                      'id': id,
                      'value': 0,
                      'constant': False,
                      'init_assign': '',
                      'rate_rule': ''})
    # parameter = dict({'SBML_type': 'AssignmentRule',
    #                   'id': id,
    #                   'rule': formula})
    xpp_variables.append(parameter)
    add_info(additional_info, id, formula)
    return xpp_variables


def make_xpp_indexed(var, index, content, name_translations, use_species,
                     xpp_variables, underscores, context):
    name = rename(var, str(index + 1), underscores)
    real_name = name_translations[name] if name in name_translations else name
    if isinstance(content, Number):
        if use_species:
            create_xpp_species(xpp_variables, real_name, content.value)
        else:
            create_xpp_parameter(xpp_variables, real_name, content.value, False)
    else:
        translator = lambda node: munge_reference(node, context, underscores)
        formula = MatlabGrammar.make_formula(content, atrans=translator)
        formula = translate_names(formula, name_translations)
        if use_species:
            create_xpp_species(xpp_variables, real_name, 0, formula)
        else:
            create_xpp_parameter(xpp_variables, real_name, 0, False, formula)


def make_xpp_raterule(assigned_var, dep_var, name_translations, index, content,
                      xpp_variables, underscores, context):
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
    if rule_var in name_translations:
        rule_var = name_translations[rule_var]
    formula = translate_names(formula, name_translations)
    add_xpp_raterule(xpp_variables, rule_var, formula)


def add_info(additional_info, id, formula):
    parameter = {'id': id, 'formula': formula}
    additional_info.append(parameter)


def create_additional_xpp_information(additional_info):
    lines=''
    for i in range(0, len(additional_info)):
        element = additional_info[i]
        id = element['id']
        if id == "t":
            lines += '{},time\n'.format(id)
        else:
            lines += '{},{}\n'.format(id, additional_info[i]['formula'])
    lines += '\n'
    return lines


def create_xpp_string(xpp_elements):
    # create the lines of the file that will be the output
    header = '#\n# This file was generated by MOCCASIN version {}.\n'.format(__version__)
    header += '# The format is suitable as input to XPP or XPPAUT.\n#\n\n'
    lines = header

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

    # output any assignments
    for i in range(0, num_objects):
        element = xpp_elements[i]
        if element['SBML_type'] == 'AssignmentRule':
            id = element['id']
            formula = element['rule']
            lines += ('# function/assignment\n')
            lines += ('{}={}\n\n'.format(id, formula))

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


def create_sbml_assigned_parameter(model, id, value, use_rule=False):
    # If creating an assignment rule for this, we want const=False in the
    # call to create the parameter.  Thus, we key off the `use_rule` arg.
    create_sbml_parameter(model, id, 0, not use_rule)
    if use_rule:
        create_sbml_assignment_rule(model, id, value)
    else:
        create_sbml_initial_assignment(model, id, value)


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


def make_indexed(var, index, content, name_translations, use_species,
                 use_rules, use_const, model, underscores, context):
    # Helper function:
    def create_species_or_parameter(the_name, the_value, const=use_const):
        if use_species:
            item = create_sbml_species(model, the_name, the_value, False)
        else:
            item = create_sbml_parameter(model, the_name, the_value, const)

    name = rename(var, str(index + 1), underscores)
    real_name = name_translations[name] if name in name_translations else name
    if isinstance(content, Number):
        is_constant = use_species and not use_rules
        create_species_or_parameter(real_name, content.value)
        return
    elif isinstance(content, Identifier):
        # Check if we have the simple case of a variable whose value is
        # *another* variable whose value in turn is a number.
        assigned_value = get_assignment(name, context)
        if assigned_value and isinstance(assigned_value, Number):
            create_species_or_parameter(real_name, assigned_value.value)
            return

    # Fall-through case: create an initial assignment.
    translator = lambda node: munge_reference(node, context, underscores)
    formula = MatlabGrammar.make_formula(content, atrans=translator)
    ast = parseL3Formula(formula)
    create_species_or_parameter(real_name, 0, False)
    if use_rules:
        create_sbml_assignment_rule(model, real_name, ast)
    else:
        create_sbml_initial_assignment(model, real_name, ast)


def make_raterule(assigned_var, dep_var, translations, index, content, model, underscores, context):
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
    if rule_var in translations:
        rule_var = translations[rule_var]
    formula = translate_names(formula, translations)
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

def create_raterule_model(parse_results, use_species=True, produce_sbml=True,
                          use_func_param_for_var_name=True, add_comments=True):
    # This assumes there's only one call to an ode* function in the file.  We
    # start by finding that call (wherever it is -- whether it's at the top
    # level, or inside some other function), then inspecting the call, and
    # saving the name of the function handle passed to it as an argument.  We
    # also save the name of the 3rd argument (a vector of initial conditions).

    reset_globals()

    # Massage the input before going any further.
    rewrite_recognized_matlab(parse_results)

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

            # FIXME: there may be more than one call in a file; if so we
            # should track down which one is relevant.  However; the current
            # code below doesn't do that -- it just takes the first one found.
            call_arglist = arglist[0]
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

    # Some people think may want to see the species/independent variables named
    # after the input parameter, and others may want it named after the output.
    if use_func_param_for_var_name:
        ode_var = dependent_var
    else:
        ode_var = assigned_var

    # If we get this far, let's start generating some code.

    if produce_sbml:
        document = create_sbml_document()
        model = create_sbml_model(document)
        compartment = create_sbml_compartment(model, 'comp1', 1)
    else:
        document = None
        model = None
        compartment = None
    xpp_variables = []
    additional_info = []

    # First wrinkle: some users want their variables named based on info they
    # write in comments.  This complicates everything that follows because we
    # have to rewrite variable names.  And we have to infer the translations
    # before we do anything else.

    name_translations = infer_real_names(working_context, ode_var, underscores)

    # Find the assignment to the initial condition variable, then create
    # either parameters or species (depending on the run-time selection) for
    # each entry.  The initial value of the parameter/species will be the
    # value in the matrix.
    init_cond = working_context.assignments[init_cond_var]
    if not isinstance(init_cond, Array):
        fail('Failed to parse the assignment of the initial value matrix')

    if produce_sbml:
        mloop(init_cond,
              lambda idx, item: make_indexed(ode_var, idx, item, name_translations,
                                             use_species, False, False, model,
                                             underscores, function_context))
    else:
        mloop(init_cond,
              lambda idx, item: make_xpp_indexed(ode_var, idx, item, name_translations,
                                                 use_species, xpp_variables,
                                                 underscores, function_context))

    # Look inside the function definition and find the assignment to the
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
    # Our problem then is to match up the 'y' variables.  We do this by
    # rewriting the individual y(1) etc. assignments, using
    # reconstruct_separate_assignments(), to put everything into a common form.

    output_var = function_context.returns[0].name
    reconstruct_separate_assignments(function_context, output_var, underscores)
    var_def = function_context.assignments[output_var]
    if not isinstance(var_def, Array):
        fail('Failed to parse the body of the function {}'.format(handle_name))

    if produce_sbml:
        mloop(var_def,
              lambda idx, item: make_raterule(ode_var, dependent_var, name_translations,
                                              idx, item, model, underscores,
                                              function_context))
    else:
        mloop(var_def,
              lambda idx, item: make_xpp_raterule(ode_var, dependent_var, name_translations,
                                                  idx, item, xpp_variables, underscores, function_context))

    # Create remaining parameters.  This breaks up matrix assignments by
    # looking up the value assigned to the variable; if it's a matrix value,
    # then the variable is turned into parameters named foo_1, foo_2, etc.
    # Also, we have to decide what to do about duplicate variable names
    # showing up inside the function body and outside.  The approach here is
    # to have variables inside the function shadow ones outside, but we
    # should really check if something more complicated is going on in the
    # Matlab code.

    skip_vars = [init_cond_var, output_var, assigned_var, ode_var]
    if isinstance(call_arglist[1], Identifier):
        # Sometimes people use an array for the time parameter.  In that case,
        # it doesn't matter for what happens below.  But if it's a named
        # variable, we want to skip it when we create the remaining vars.
        skip_vars.append(call_arglist[1].name)
    # for i in range(3,len(call_arglist)):
    #     skip_vars.append(call_arglist[i].name)
    create_remaining_vars(working_context, function_context, skip_vars,
                          xpp_variables, name_translations, model,
                          underscores, produce_sbml, additional_info)

    # Deal with final quirks.
    global GLOBALS
    if GLOBALS['need time']:
        if produce_sbml:
            create_sbml_assigned_parameter(model, "t", parseL3Formula("time"), True)
        else:
            # xpp automatically assumes 't' is time so no need to tell it
            create_xpp_parameter(xpp_variables, 't', 0, False)
            add_info(additional_info, 't', '')

    # Write the SBML.
    if produce_sbml:
        writer = SBMLWriter();
        if add_comments:
            writer.setProgramName("MOCCASIN")
            writer.setProgramVersion(__version__)
        sbml = writer.writeSBMLToString(document);
    else:
        sbml = create_xpp_string(xpp_variables)

    # Finally, return the model, with extra info about things that may need
    # to be added back in post-processing.
    return [sbml, additional_info]


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


def create_remaining_vars(working_context, function_context, skip_vars,
                          xpp_variables, name_translations, model, underscores,
                          produce_sbml, additional_info):

    all_vars = dict(itertools.chain(working_context.assignments.items(),
                                    function_context.assignments.items()))

    # We do it slightly differently if the variable is assigned inside the
    # ODE function versus outside.  Inside, we make them assignment rules
    # because the values would normally be recomputed every time the function
    # is called.  Outside, we make them one-time initial assignments.

    for var, rhs in all_vars.items():
        if var in skip_vars: continue
        if name_is_structured(var): continue  # FIXME doesn't handle matrices on LHS.
        in_function = True if var in function_context.assignments else False

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
                translated = translate_names(rhs.name, name_translations)
                ast = parseL3Formula(translated)
                create_sbml_assigned_parameter(model, var, ast, in_function)
            else:
                # Can't do that in XPP output.  Check if we can subsitute.
                assigned_value = get_assignment(rhs.name, function_context)
                if isinstance(assigned_value, Number):
                    result = assigned_value.value
                else:
                    if assigned_value:
                        formula_parser = NumericStringParser()
                        result = formula_parser.eval(assigned_value)
                    else:
                        substituted = substitute_vars(assigned_value, working_context)
                        formula = MatlabGrammar.make_formula(substituted, atrans=translator)
                        if formula:
                            translated = translate_names(rhs.name, name_translations)
                            result = formula_parser.eval(translated)
                        else:
                            # Not sure what else to do here.
                            result = rhs.name
                create_xpp_parameter(xpp_variables, var, result)
        elif isinstance(rhs, Array):
            if produce_sbml:
                mloop(rhs,
                      lambda idx, item: make_indexed(var, idx, item, name_translations, False,
                                                     in_function, not in_function,
                                                     model, underscores, function_context))
            else:
                mloop(rhs,
                      lambda idx, item: make_xpp_indexed(var, idx, item, name_translations, False,
                                                         xpp_variables, underscores,
                                                         function_context))
        elif isinstance(rhs, ArrayRef) or isinstance(rhs, list) \
             or isinstance(rhs, FunCall) or isinstance(rhs, Expression):
            # Inefficient way to do this, but for now let's just do this.
            if isinstance(rhs, ArrayRef):
                rhs = rhs.args
            if isinstance(rhs, FunCall):
                rhs = [rhs]
            if isinstance(rhs, Expression):
                rhs = rhs.content
            translator = lambda node: munge_reference(node, function_context,
                                                      underscores)
            if produce_sbml:
                formula = MatlabGrammar.make_formula(rhs, atrans=translator)
                translated = translate_names(formula, name_translations)
                ast = parseL3Formula(translated)
                if ast:
                    create_sbml_assigned_parameter(model, var, ast, in_function)
            else:
                if in_function:
                    formula = MatlabGrammar.make_formula(rhs, atrans=translator)
                    translated = translate_names(formula, name_translations)
                    create_xpp_assignment(xpp_variables, var, translated, additional_info)
                else:
                    substituted = substitute_vars(rhs, working_context)
                    formula = MatlabGrammar.make_formula(substituted, atrans=translator)
                    # horrible hack to not look at a function used odeset
                    if formula.startswith('odeset') or formula.startswith('(odeset'):
                        continue;

                    if formula:
                        translated = translate_names(formula, name_translations)
                        formula_parser = NumericStringParser()
                        result = formula_parser.eval(translated)
                        if result:
                            create_xpp_parameter(xpp_variables, var, result)
        elif isinstance(rhs, FunHandle):
            # Skip function handles. If any was used in the ode* call, it will
            # have been dealt with earlier.
            continue


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


# This is currently oriented towards detecting comments like this:
#
#    function y = foo(t, x)
#
#    % x(1)  [IFNb_mRNA]
#    y(1)=  r1*myf- k1*x(1);
#    % x(2)  [IFNb_env]
#    y(2)=   r2*x(1)/(KK2+x(1));
#
# where the comments include a mention of the variable name and a symbol.  It
# ignores non-alphanumeric characters between the "x(n)" text and subsequent
# text.  It will get it wrong if there's any text between "x(n)" and the
# intended label.
#
# The approach of looking at all comments has the advantage that it doesn't
# require comments to be right in front or behind the variable being named.
# The comments could thus appear as a block somewhere, or be interpersed with
# the matlab code, or whatever.  It does have the disadvantage that it can
# get confused by comments that mention "x(n") in other contexts.
#
# FIXME: develop a systematic format for these comments and tell users about it.

def infer_real_names(context, ode_var, underscores):
    # Walk down the list of nodes for the file, looking for comments.
    # For every comment, look for any that mention the ode variable.
    # Returns a dictionary of translations.
    translations = {}
    if not context.parent or not context.parent.nodes:
        return translations
    for node in context.parent.nodes:
        if not isinstance(node, Comment):
            continue
        match = re.search(ode_var + r'\((\d+)\)\s+(\S+)', node.content)
        if not match:
            continue
        # Found a match.
        index = match.group(1)          # The number inside "x(n)"
        found = match.group(2)          # The rest of the line after "x(n)"
        guess = re.sub(r'(\W+)(\w+)(\W+)', r'\2', found)
        if guess and valid_id(guess):
            our_name = ode_var + '_'*underscores + index
            translations[our_name] = guess
    return translations


def translate_names(text, translations):
    for oldname, newname in translations.items():
        text = text.replace(oldname, newname)
    return text


# -----------------------------------------------------------------------------
# Post-processing output from BIOCHAM web service.
# -----------------------------------------------------------------------------

def process_biocham_output(sbml, parse_results, extra_info):
    if not sbml:
        return sbml
    document = SBMLReader().readSBMLFromString(sbml)
    if not document:
        return sbml
    model = document.getModel()
    if not model:
        return sbml
    if parse_results.functions:
        id = list(parse_results.functions.keys())[0]
        model.setId(id)
        model.setName(id + ' translated by MOCCASIN')

    # Start by converting Biocham's L2v2 model to L3v1.
    success = document.setLevelAndVersion(3, 1)
    if not success:
        return sbml
    # Clear the units that are automatically added by the previous call.
    document.getModel().unsetTimeUnits()
    document.getModel().unsetSubstanceUnits()
    document.getModel().unsetExtentUnits()
    document.getModel().unsetLengthUnits()
    document.getModel().unsetVolumeUnits()
    document.getModel().unsetAreaUnits()
    for i in range(document.getModel().getNumUnitDefinitions(), 0, -1):
        document.getModel().removeUnitDefinition(i - 1)
    for i in range(document.getModel().getNumCompartments(), 0, -1):
        document.getModel().getCompartment(i - 1).unsetUnits()
    for i in range(document.getModel().getNumSpecies(), 0, -1):
        document.getModel().getSpecies(i - 1).unsetSubstanceUnits()

    # Deal with special cases.
    for record in extra_info:
        # Special case for 't':
        if record['id'] == "t":
            create_sbml_assignment_rule(model, "t", parseL3Formula("time"))
            param = model.getParameter('t')
            param.setConstant(False)
            continue
        # All others: create an assignment rule with a formula.
        id = record['id']
        ast = parseL3Formula(record['formula'])
        if ast:
            create_sbml_assignment_rule(model, id, ast)
            # Make sure to change the parameter to non-constant
            param = model.getParameter(id)
            param.setConstant(False)
    return writeSBMLToString(document)


# -----------------------------------------------------------------------------
# MATLAB rewriter
#
# This rewrites some simple MATLAB constructs to something we can deal with.
# -----------------------------------------------------------------------------

class MatlabRewriter(MatlabNodeVisitor):
    def visit_FunCall(self, node):
        if isinstance(node.name, Identifier):
            func = node.name.name
            if func in matlab_converters:
                return matlab_converters[func](node)
        return node

    def visit_Identifier(self, node):
        # Assume this is a reference to time.
        if node.name == "t":
            global GLOBALS
            GLOBALS['need time'] = True
        return node

    def visit_Assignment(self, node):
        node.rhs = self.visit(node.rhs)
        return node


def rewrite_recognized_matlab(context):
    rewriter = MatlabRewriter()
    for lhs, rhs in context.assignments.items():
        context.assignments[lhs] = rewriter.visit(rhs)
    for name, args in context.calls.items():
        context.calls[name] = rewriter.visit(args)
    for function_name, function_context in context.functions.items():
        rewrite_recognized_matlab(function_context)


# E.g.: zeros(3,1) produces a matrix
def matlab_zeros(thing):
    args = thing.args
    if len(args) == 1:
        rows = int(args[0].value)
        return Array(rows=[[Number(value='0')]]*rows, is_cell=False)
    elif len(args) == 2:
        rows = int(args[0].value)
        cols = int(args[1].value)
        return Array(rows=[[Number(value='0')]*cols]*rows, is_cell=False)
    # Fall back: make sure to return *something*.
    return thing


# Matlab's log(x) is natural log of x, but libSBML's parser defaults to
# base 10.
def matlab_log(thing):
    args = thing.args
    if len(args) == 1:
        return FunCall(name=Identifier(name="ln"), args=[args[0]])
    # Fall back: make sure to return *something*.
    return thing


matlab_converters = {
    'zeros': matlab_zeros,
    'log': matlab_log
}


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

def get_filename_and_options(argv):
    help_msg = 'MOCCASIN version ' + __version__ + '\n' + main.__doc__
    try:
        options, path = getopt.getopt(argv[1:], "cdpqxorvl")
    except:
        raise SystemExit(help_msg)
    if len(path) != 1 or len(options) > 8:
        raise SystemExit(help_msg)
    include_comments  = not any(['-c' in y for y in options])
    debug             = any(['-d' in y for y in options])
    quiet             = any(['-q' in y for y in options])
    print_parse       = any(['-x' in y for y in options])
    print_raw         = any(['-r' in y for y in options])
    use_species       = not any(['-p' in y for y in options])
    use_param_as_name = not any(['-l' in y for y in options])
    create_sbml       = not any(['-o' in y for y in options])
    return path[0], debug, quiet, print_parse, print_raw, use_species, \
        use_param_as_name, create_sbml, include_comments


def main(argv):
    '''Usage: converter.py [options] FILENAME.m
Available options:
 -c   Omit comments in the SBML file about program version and other info
 -d   Drop into pdb before starting to parse the MATLAB input
 -h   Print this help message and quit
 -l   Name variables per ODE function's output variable (default: use its parameters)
 -o   Convert to XPP .ode file format (default: produce SBML)
 -p   Turn variables into SBML parameters (default: make them SBML species)
 -q   Be quiet; just produce the final output, nothing else
 -r   Print the raw MatlabNode output for the output printed with option -x
 -x   Print extra debugging info about the interpreted MATLAB
'''
    path, debug, quiet, print_parse, print_raw, use_species, use_param_as_name, \
        create_sbml, include_comments = get_filename_and_options(argv)

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

    [sbml, additional] = create_raterule_model(parse_results, use_species,
                                               create_sbml, use_param_as_name,
                                               include_comments)

    if print_parse and not quiet:
        print('')
        print('----- interpreted output ' + '-'*50)
        parser.print_parse_results(parse_results, print_raw)

    if not quiet:
        print('')
        if create_sbml:
            print('----- SBML output ' + '-'*50)
        else:
            print('----- XPP output ' + '-'*50)

    print(sbml)


def fail(msg):
    raise SystemExit(msg)


if __name__ == '__main__':
    main(sys.argv)
