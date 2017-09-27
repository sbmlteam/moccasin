#!/usr/bin/env python3.4
#
# @file    converter.py
# @brief   MATLAB converter
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

# Basic principles of this converter
# ----------------------------------
#
# The conversion code in this file produces either "rate rule" style SBML,
# or XPP/XPPAUT output (which can only express a "rate rule" style of model).
# Here's the basic approach.
#
# Matlab's ode* functions handle the following general problem:
#
#     Given a set of differential equations (with X denoting a vector),
#         dX/dt = f(t, X)
#     with initial values X(t_0) = xinit,
#     find the values of the variables X at different times t.
#
# The function defining the differential equations is given as "f" in a call
# to a MATLAB ode* function such as ode45.  For MOCCASIN, we assume there's
# only one call to an ode* function in the file.  We assume the user provides
# a MATLAB file that has a structure more or less such as the following
# example (and here, the specific formula in the function "f" is just an
# example -- our code does not depend on the details of the function, and
# this is merely a realistic example from a real use case):
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
# In the above, the function "f" passed to MATLAB's ode45 is the function "f"
# in the general problem statement.  The body of "f" defines a vector of
# formulas for dx/dt for each variable x. The values of x at different times
# t is what the ode45 function computes.
#
# In create_raterule_model(), we translate this into one of the following,
# depending on the options handed to the function:
#
# 1. An SBML format that uses "rate rules" to directly encode the dx/dt
#    expressions.  This uses the name of the variable in the LHS matrix used
#    in the assignment of the call to ode45 as the name of the independent
#    variable.  So in other words, in the sample above, "x" will be the basis
#    of the species or parameter names and the rate rules generated because
#    that's what is used in [t, x] =...
#
# 2. An XPP format that captures the parameters and dx/dt expressions.  This
#    is the same thing as an SBML model that uses direct expression of ODEs
#    instead of SBML's reaction construct.

# Preface material.
# .............................................................................

from __future__ import print_function
from libsbml import *
from pyparsing import ParseException, ParseResults

import getopt
import glob
import itertools
from natsort import natsorted, ns
import operator
import re
import six
import sys

sys.path.append('..')

from matlab_parser import *
from version import __version__, __url__
try:
    from .cleaner import *
    from .errors import *
    from .evaluate_formula import *
    from .expr_tester import *
    from .finder import *
    from .name_generator import *
    from .recognizer import *
    from .rewriter import *
    from .xpp import *
except:
    from cleaner import *
    from errors import *
    from evaluate_formula import *
    from expr_tester import *
    from finder import *
    from name_generator import *
    from recognizer import *
    from rewriter import *
    from xpp import *


# -----------------------------------------------------------------------------
# MATLAB parsing-related stuff.
# -----------------------------------------------------------------------------

def parse_matlab(path):
    """Invokes the MatlabGrammar parser on the file given by 'path'."""
    try:
        with MatlabGrammar() as parser:
            return parser.parse_file(path)
    except Exception as err:
        # FIXME test what happens here
        fail(MatlabParsingError, err)


def sanity_check_matlab(parse_results):
    """Perform basic checks on the parsed MATLAB input, and return errors
    if the MATLAB is of a form that we cannot currently convert.  This function
    returns a tuple, (usable, message), where 'usable' is a Boolean that is
    True if no obvious problems were found and 'message' is a string that
    describes the problem, if there is one.
    """
    # There must be at least one function call in the file.
    if not parse_results.calls and not parse_results.functions:
        fail(NotConvertibleError, 'no function calls found => no calls to odeNN')

    # There must be one, and only one, call to a MATLAB odeNN function in the
    # highest context, or else we won't know what to do.
    context = first_function_context(parse_results)
    calls = [(k,v) for k,v in context.calls.items() if k.name.startswith('ode')]
    calls = [(k,v) for k,v in calls if not k.name.startswith('odeset')]
    if not calls:
        fail(NotConvertibleError, 'did not find call to MATLAB odeNN function')
    if len(calls) > 1:
        fail(NotConvertibleError, 'multiple calls to odeNN functions')

    # We have one call to an odeNN function.  It will have at least 3 args:
    #     [t, y] = ode45(@f, tspan, x0)
    matlab_func = calls[0][0]       # Name of the odeNN function.
    args        = calls[0][1][0]
    ode_func    = args[0]           # Handle to a function defining the ODEs.
    init_cond   = args[2]           # Initialization conditions.

    # Currently, we only allow a variable as the initial conditions parameter.
    if not isinstance(init_cond, Identifier):
        fail(UnsupportedInputError,
             'unsupported type of initial conditions variable in ODE call')

    # We currently can't handle anything other than function handles or
    # anonymous functions in the arguments to the odeNN functions.  If there
    # is no function definition in this file, the function passed to the
    # odeNN call can only be an anonymous function handle (or else, the
    # function passed is not defined in this file).  We do watch out for the
    # case where the handle is stored in a variable.
    if isinstance(ode_func, Identifier):
        ode_func = assignment(ode_func, context)
    if not isinstance(ode_func, AnonFun) and not isinstance(ode_func, FuncHandle):
        fail(UnsupportedInputError,
             'unsupported type of argument to {} call'.format(matlab_func.name))
    if len(parse_results.functions) == 0:
        if isinstance(ode_func, AnonFun):
            return
        elif isinstance(ode_func, FuncHandle):
            fail(IncompleteInputError,
                 'missing definition of function passed in odeNN call')

    # If the user's ODE definition is a function, that function might be
    # defined nested inside the first function in the file, or it might be a
    # separate (parallel) function defined in the file.  Look for it.
    if not parse_results.name:
        # Case 1: a script.  Look for the ODE function definition at the top.
        scopes = [parse_results]
    else:
        # Case 2: the file is a function definition file.  Now it's trickier:
        # the ODE function might be nested inside this one, or the file might
        # contain multiple parallel functions.  We look everywhere.
        if parse_results.name not in parse_results.functions:
            # This is a WTF case.
            fail(UnsupportedInputError,
                 'input file is not structured in a supported form')
        scopes = [parse_results.functions[parse_results.name], parse_results]
    if isinstance(ode_func, FuncHandle):
        if not isinstance(ode_func.name, Identifier):
            fail(UnsupportedInputError,
                 'function passed to odeNN is not a simple handle')
        for s in scopes:
            if ode_func.name in s.functions:
                break
        else:
            fail(IncompleteInputError,
                 'function passed to odeNN is not defined in this file')


def clean_matlab(context, protected_context):
    '''Remove MATLAB content we would ignore anyway.  This speeds up processing
    and prevents having to do more complicated checks later to figure out if
    variable are needed in the final output.'''

    def remove_unused_assignments(context):
        # Recursive helper function used below.
        assigned_vars = []
        for lhs, rhs in context.assignments.items():
            if isinstance(lhs, Identifier):
                assigned_vars.append(lhs)
            if isinstance(lhs, Array):
                subscripts = lhs.rows[0]
                for elem in subscripts:
                    if isinstance(elem, Identifier):
                        assigned_vars.append(elem)
        used_vars = [x for x in assigned_vars if MatlabFinder(context).find_use(x)]
        unused_vars = list(set(assigned_vars) - set(used_vars))
        for var in list(context.assignments.keys()):
            if var in unused_vars:
                context.assignments.pop(var)
            if isinstance(var, Array):
                subscripts = var.rows[0]
                for elem in subscripts:
                    if elem not in unused_vars:
                        break
                else:
                    # All subscripts are in unused_vars => remove the array
                    context.assignments.pop(var)

        # Recursively visit inner function definitions.
        for fname, fcontext in context.functions.items():
            if fname == protected_context.name:
                continue
            remove_unused_assignments(fcontext)

    # Remove MATLAB content we can't do anything about, like plotting commands.
    context.nodes = MatlabCleaner().visit(context.nodes)
    # Remove assignments to variables that are never used in the code.  (This
    # might happen if variables are only used for plotting purposes.)
    remove_unused_assignments(context)


def rewrite_matlab(context, format):
    '''Rewrite some constructs into things we can use.'''
    context.nodes = MatlabRewriter(context, format).visit(context.nodes)


def first_function_context(context):
    """If there is at least one function definition in the given context, it
    returns the topmost or first function's context.  If there are no function
    definitions in the context, it returns the given context.
    """
    if not context or not context.topmost:
        # Really we should never get called in these cases.
        return None
    elif context.name in context.functions:
        return function_declaration(context.name, context)
    else:
        # We don't have a function definition, so treat this file as a script.
        return context


def all_function_calls(context):
    """Create a dictionary of all function calls contained in the given
    context, recursively descending into the contexts of any function
    definitions too.  The dictionary keys are the names of the functions
    being called.
    """
    calls = {}
    for fname, arglist in context.calls.items():
        calls[fname] = arglist
    for fname, fcontext in context.functions.items():
        calls.update(all_function_calls(fcontext))
    return calls


def matlab_ode_call(context):
    '''Find and return the function call to the MATLAB odeNN function.'''
    # FIXME: there may be more than one ode call.  We should track down which
    # one is relevant.  The current code below just takes the first one found.
    ode_function = None
    call_arglist = None
    calls = all_function_calls(context)
    for id, arglist in calls.items():
        if isinstance(id, Identifier) and re.match('^ode[0-9]', id.name):
            return id, arglist[0]
    # This should not happen if sanity_check_matlab() did its job.
    fail(NotConvertibleError, 'did not find call to MATLAB odeNN function')


def function_declaration(name, context, recursive=False):
    '''Finds and returns the FunDecl object for "name".'''
    if context and name in context.functions:
        return context.functions[name]
    elif recursive and context.parent:
        return function_declaration(name, context.parent, recursive)
    else:
        return None


def assignment(thing, context, recursive=False):
    '''Returns the value assigned to the given 'thing'.  If the value is an
    Identifier and 'recursive' is non-False, looks up the Identifier's value
    recursively, until it gets something that's not an Identifier.
    '''
    if thing in context.assignments:
        value = context.assignments[thing]
        if isinstance(value, Identifier) and recursive:
            return assignment(value, context, recursive)
        else:
            return value
    elif hasattr(context, 'parent') and context.parent:
        return assignment(thing, context.parent)
    else:
        return None


def all_assignments(context):
    '''Returns a dictionary of all assignments in the given context,
    recursively looking inside function contexts within the given context.
    '''
    assignments = {}
    for var, rhs in context.assignments.items():
        assignments[var] = rhs
    for fname, fcontext in context.functions.items():
        assignments.update(all_assignments(fcontext))
    return assignments


def assigned_ode_var(name, context):
    # We are looking for something of this form:
    # [t, y] = ode45(arg, arg, arg, ...)
    for lhs, rhs in context.assignments.items():
        if isinstance(rhs, FunCall) or isinstance(rhs, Ambiguous):
            if isinstance(rhs.name, Identifier) and rhs.name == name:
                if not isinstance(lhs, Array) or len(lhs.rows[0]) != 2:
                    fail(UnsupportedInputError, 'unrecognized form of odeNN call')
                # Arrays on LHS can only have one row, so using [0] is safe.
                return lhs.rows[0][1]
    # Something in our algorithm is wrong, if we get here.
    fail(ConversionError, 'found odeNN call, but could not interpret it')


def num_underscores(context):
    '''Looks at identifiers to see if any uses underscores underscores in the
    name.  Counts the longest sequence of underscores found and returns that
    number.  Recursively looks in subcontexts too.
    '''
    longest = 0
    for lhs in context.assignments.keys():
        if isinstance(lhs, Identifier) and '_' in lhs.name:
            this_longest = len(max(re.findall('(_+)', lhs.name), key=len))
            longest = max(longest, this_longest)
        if isinstance(lhs, Array):
            # Arrays on LHS can only have one row, so using [0] should be safe.
            for thing in lhs.rows[0]:
                if isinstance(thing, Identifier) and '_' in thing.name:
                    this_longest = len(max(re.findall('(_+)', thing.name), key=len))
                    longest = max(longest, this_longest)
    if context.functions:
        for subcontext in six.itervalues(context.functions):
            longest = max(num_underscores(subcontext), longest)
    return longest


def ref_name(name, context):
    '''Looks through assignments to see if time is ever referenced explicitly.'''
    searcher = MatlabRecognizer(context)
    # The principle here is that it wouldn't make sense for a model to assign
    # to time, so we only need to check if time is referenced in the RHS.
    for lhs, rhs in context.assignments.items():
        searcher.visit(rhs)
        if searcher.found(name):
            return True
    return False


def func_from_handle(thing, context, underscores):
    '''Retrieves the function called by a function handle.  Returns a tuple,
       (ignorable_variable, function_name)
    where "ignorable_variable" is an intermediate variable that may have
    held a function handle.  If it is None, then there was no intermediate
    variable.'''
    # Cases:
    #  @foo => foo is the function name
    #  @(args)body => several cases possible:
    #   - body is a variable that holds another function handle => chase it
    #   - body is a function call => return the function name
    #   - body is a matrix
    ignorable_variable = None
    if isinstance(thing, FuncHandle):
        # Case: ode45(@foo, time, xinit, ...)
        # The item has to be an identifier -- MATLAB won't allow anything else.
        return (None, thing.name)
    elif isinstance(thing, Identifier):
        # Case: ode45(somevar, trange, xinit, ...)
        # Look up the value of somevar and see if that's a function handle.
        if thing in context.assignments:
            value = context.assignments[thing]
            if isinstance(value, FuncHandle):
                # The name of the handle must be an identifier, so dereference it.
                return (thing, value.name)
            elif isinstance(value, AnonFun):
                # Reset thing to the body and fall through to the AnonFun case.
                ignorable_variable = thing
                thing = value
            else:
                # Variable value is not a function handle.
                return (None, None)
        else:
            # Looks like a variable, but we don't know its value.
            fail(NotConvertibleError, '{} is unknown'.format(thing.name))

    # This next thing is not an else-if because may get here two different ways.
    if isinstance(thing, AnonFun):
        # Case: ode45(@(args)..., time, xinit)
        if isinstance(thing.body, FunCall) or isinstance(thing.body, Ambiguous):
            # Body is just a function call.
            if isinstance(thing.body.name, Identifier):
                # The name is a plain identifier -- good.
                return (ignorable_variable, thing.body.name)
            else:
                # The function name is not an identifier but more complicated,
                # perhaps a struct.  Currently, we can't deal with it.
                return (None, None)
        elif isinstance(thing.body, Array):
            # Body is an array.  In our domain of ODE and similar models, it
            # means it's the equivalent of a function body.  Approach: create
            # a new fake function, store it, and return its name.
            return (ignorable_variable,
                    create_array_function(thing, context, underscores))
    else:
        return (None, None)


def create_array_function(thing, context, underscores):
    if not isinstance(thing, AnonFun):
        # Shouldn't be here in the first place.
        return None
    args = thing.args
    func_name = NameGenerator().name(prefix='anon')
    func_id = Identifier(name=func_name)
    output_var_name = func_name + '_'*underscores + 'out'
    output_var = Identifier(name=output_var_name)
    newcontext = MatlabContext(func_id, context, None, args, [output_var])
    newcontext.assignments[output_var] = thing.body
    newcontext.types[output_var] = 'variable'
    for var in args:
        newcontext.types[var] = 'variable'
    context.functions[func_id] = newcontext
    return func_id


def constant_expression(node, context):
    tester = MatlabExprTester(context)
    tester.visit(node)
    return tester.is_constant()


# -----------------------------------------------------------------------------
# Abstract functions for both SBML and XPP output.
# -----------------------------------------------------------------------------

def blank_document(output_format="sbml"):
    '''Create a blank data structure for the output to be generated.  Parameter
    "output_format" indiates the format of the output: "sbml" means SBML,
    "xpp" means true XPP, and "biocham" means XPP intended for the BIOCHAM web
    service.
    '''
    if output_format == "sbml":
        document = create_sbml_document()
        model = create_sbml_model(document)
        create_sbml_compartment(model, 'comp1', 1)
        return document
    else:
        return XPPDocument(output_format)


def create_species(document, id, value, constant):
    if isinstance(document, XPPDocument):
        create_xpp_species(document, id, value)
    else:
        create_sbml_species(document.getModel(), id, value, constant)


def create_parameter(document, id, value, constant):
    if isinstance(document, XPPDocument):
        create_xpp_parameter(document, id, value, constant)
    else:
        create_sbml_parameter(document.getModel(), id, value, constant)


def create_assigned_parameter(document, id, value, use_rule=False):
    # If creating an assignment rule for this, we want const=False in the
    # call to create the parameter.  Thus, we key off the `use_rule` arg.
    create_parameter(document, id, 0, not use_rule)
    create_assignment(document, id, value, use_rule)


def create_assignment(document, id, formula, use_rule=False):
    func = create_assignment_rule if use_rule else create_initial_assignment
    func(document, id, formula)


def create_initial_assignment(document, id, formula):
    if isinstance(document, XPPDocument):
        # Biocham uses SBML assignment rules for what should be initial
        # assignments, and moreover, does not support the real XPP equivalent
        # for assignment rules -- a double whammy.  See the longer discussion
        # in the section below on XPP-specific things.  We have to
        # post-process Biocham's output to convert certain assignment rules
        # into what we meant to be initial assignments.
        create_xpp_initial_assignment(document, id, formula)
        document.post_convert.append((id, formula))
    else:
        ast = parseL3Formula(formula)
        create_sbml_initial_assignment(document.getModel(), id, ast)


def create_assignment_rule(document, id, formula):
    if isinstance(document, XPPDocument):
        create_xpp_assignment_rule(document, id, formula)
    else:
        ast = parseL3Formula(formula)
        create_sbml_assignment_rule(document.getModel(), id, ast)


def create_rate_rule(document, id, formula):
    if isinstance(document, XPPDocument):
        create_xpp_rate_rule(document, id, formula)
    else:
        ast = parseL3Formula(formula)
        create_sbml_rate_rule(document.getModel(), id, ast)


# -----------------------------------------------------------------------------
# XPP-specific stuff
# -----------------------------------------------------------------------------
#
# The following table summarizes the XPP equivalent constructs for SBML
# components generated by this converter.  This first table is for the
# general case of XPP output; this is *not* what we do for the XPP we send to
# Biocham -- see further below for the Biocham case.
#
#             Assignment        Type of   XPP               SBML ODE-style
# Thing	      location          value     construct         equivalent
# --------    ----------------  --------  ---------------   -------------
# ode var     inside ode func   number    init X=val        species value="val"
# ode var     inside ode func   formula   dX/dt=f(X)        species rate rule
#
# ode var     outside ode func  N/A       N/A               N/A
#
# other var   inside ode func   number    parameter y=val   parameter value="val"
# other var   inside ode func   formula   y=formula         assignment rule
#
# other var   outside ode func  number    parameter y=val   parameter value="val"
# other var   outside ode func  formula   !y=formula        initial assignment
#
# For Biocham, we have to limit ourselves to the subset of XPP understood by
# BIOCHAM 3.7.  BIOCHAM only understands the following XPP syntax:
#    parameter k=value      # constant parameter
#    !y=formula             # parameter with assignment
#    init X=value           # initial value for dynamic variable in ODE
#    dX/dt=f(X)             # ODE, or SBML's rate rule.
#
# What's missing?  That's where things get confusing.  The "y=formula" is
# missing, which is the equivalent of SBML's assignment rules, *however*, it
# turns out that Biocham turns "!y=formula" into assignment rules rather than
# initial assignments.  In other words, it flips assignment rules and initial
# assignments.  So what we have to do for Biocham is construct a different
# version of XPP where we use "!y=formula" instead of "y=formula" (to get
# assignment rules for what we do want to be assignment rules) and
# post-process the Biocham output to convert assignment rules that are
# *supposed* to be initial assignments.
#
#             Assignment         Type of   XPP
# Thing	      location           value     construct
# --------    -----------------  --------  ---------
# ode var     inside ode func    number    init X=value
# ode var     inside ode func    formula   dX/dt=f(X)
#
# ode var     outside ode func   N/A       N/A
#
# other var   inside ode func    number    parameter A=value
# other var   inside ode func    formula   !A=formula       <--- we change this
#
# other var   outside ode func   number    parameter A=value
# other var   outside ode func   formula   !A=formula       <--- post process
#

def create_xpp_species(document, id, value):
    document.vars.append(XPPVar(type='species', id=id, init_value=value))


def create_xpp_parameter(document, id, value, constant=True):
    document.vars.append(XPPVar(type='parameter', id=id, constant=constant,
                                init_value=value))


def create_xpp_initial_assignment(document, id, formula):
    # Unlike with SBML, XPP doesn't need separate parameter declaration and
    # assignment.  If we've already declared the parameter, update the fields.
    var = next((v for v in document.vars if v.id == id), None)
    var.init_assign = formula


def create_xpp_assignment_rule(document, id, formula):
    # Unlike with SBML, XPP doesn't need separate parameter declaration and
    # assignment.  If we've already declared the parameter, update the fields.
    var = next((v for v in document.vars if v.id == id), None)
    var.constant = False
    var.assign_rule = formula


def create_xpp_rate_rule(document, id, formula):
    # Unlike with SBML, XPP doesn't need separate parameter declaration and
    # assignment.  If we've already declared the parameter, update the fields.
    var = next((v for v in document.vars if v.id == id), None)
    var.constant = False
    var.rate_rule = formula


def generate_xpp_string(document, add_comments):
    '''Generate the final XPP output.'''
    lines = generate_xpp_header(add_comments)
    vars = document.vars

    # Constant "par" parameters.
    # We do these in sorted order so the output is easier to read.  The
    # order can't matter in this case -- they're numerical constants.
    for var in natsorted(filter(lambda v: v.constant and not v.init_assign, vars),
                         key=lambda v: v.id.lower()):
        type = 'Parameter'
        form = 'par '
        value = var.init_value
        note = 'constant'
        lines += '# {} id = {}, {}.\n'.format(type, var.id, note)
        lines += '{}{}={}\n'.format(form, var.id, value)
        lines += '\n'

    # The rest are not sorted because XPP says that the order of fixed '!'
    # variables is meaningful.

    for var in filter(lambda v: v.constant and v.init_assign, vars):
        type = 'Parameter'
        form = '!'
        value = var.init_assign
        note = 'constant, set by an initial assignment'
        if document.xpp_subset == "biocham":
            note = 'set by assignment rule, but should be initial assignment'
        lines += '# {} id = {}, {}.\n'.format(type, var.id, note)
        lines += '{}{}={}\n'.format(form, var.id, value)
        lines += '\n'

    # Non-constant parameters with assignment rules.
    for var in filter(lambda v: v.assign_rule, vars):
        type = 'Variable'
        note = 'defined by an assignment rule'
        form = ''
        if document.xpp_subset == "biocham":
            form = '!'
            note = 'defined by what Biocham treats as an assignment rule'
        lines += '# {} id = {}, {}.\n'.format(type, var.id, note)
        lines += '{}{}={}\n'.format(form, var.id, var.assign_rule)
        lines += '\n'

    for var in filter(lambda v: v.rate_rule, vars):
        type = 'Species' if var.type == 'species' else 'Variable'
        note = 'defined by a rate rule'
        lines += '# {} id = {}, {}.\n'.format(type, var.id, note)
        lines += 'init {}={}\n'.format(var.id, var.init_value)
        lines += 'd{}/dt={}\n'.format(var.id, var.rate_rule)
        lines += '\n'

    lines += 'done\n'
    return lines


def generate_xpp_header(add_comments):
    lines = ''
    if add_comments:
        lines += '#\n# This file was generated automatically by MOCCASIN '
        lines += 'version {}.\n'.format(__version__)
        lines += '# The contents are suitable as input to the program XPP or XPPAUT.\n'
        lines += '# For more information about MOCCASIN, please visit the website:\n'
        lines += '# {}\n#\n\n'.format(__url__)
    return lines


# -----------------------------------------------------------------------------
# SBML-specific stuff.
# -----------------------------------------------------------------------------
#
# Quick summary of how we convert different types of variables in the MATLAB
# model.  We have two possible types of varables: "ODE variables", which are
# the output variables of the user's ODE function, and any other variables.
# (Some of those other variables may be meant to be constant, but in MATLAB
# you can't distinguish between constants and variables, so as far as we're
# concerned, they may all be variables -- just not the same variables as the
# ODE varibles.) The table below shows the correspondences to SBML terminology.
#
#                                  Type of    Initial      Assignment  Rate
# Thing	      Assignment location  value      assignment?  rule?       rule?
# --------    -------------------  --------   -----------  ---------   -----
# ode var     inside ode func      number     no           no          yes
# ode var     inside ode func      formula    no           no          yes
#
# ode var     outside ode func     N/A        N/A          N/A         N/A
#
# other var   inside ode func      number     no           no          no
# other var   inside ode func      formula    no           yes         no
#
# other var   outside ode func     number     no           no          no
# other var   outside ode func     formula    yes          no          no

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
    check(c.setName(id),             'set compartment name')
    check(c.setConstant(const),      'set compartment "constant"')
    check(c.setSize(float(size)),    'set compartment "size"')
    check(c.setSpatialDimensions(3), 'set compartment dimensions')
    return c


def create_sbml_species(model, id, value, const=False):
    comp = model.getCompartment(0)
    s = model.createSpecies()
    check(s,                                       'create species')
    check(s.setId(id),                             'set species id')
    check(s.setName(id),                           'set species name')
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
    check(p.setName(id),            'set parameter name')
    check(p.setConstant(const),     'set parameter "constant"')
    check(p.setValue(float(value)), 'set parameter value')
    return p


def create_sbml_initial_assignment(model, id, ast):
    ia = model.createInitialAssignment()
    check(ia,               'create initial assignment')
    check(ia.setMath(ast),  'set initial assignment formula')
    check(ia.setSymbol(id), 'set initial assignment symbol')
    return ia


def create_sbml_rate_rule(model, id, ast):
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


def sort_sbml_parameters(model):
    '''Sort the list of parameters inside the SBMLDocument.
    Code originally in part by Frank Bergmann.
    '''
    # We get the parameters, remove them from the model, sort our list, and
    # reinsert the parameters into the model in sorted order.
    unsorted = []
    parameters = model.getListOfParameters()
    for i in range(0, parameters.size()):
        unsorted.append(parameters.remove(0))

    # Write it back to the model, but in sorted order
    for item in natsorted(unsorted, key=lambda x: x.getId().lower()):
        parameters.appendAndOwn(item)


# -----------------------------------------------------------------------------
# Inference of names from comments.
# -----------------------------------------------------------------------------
#
# This is a start at renaming variables based on comments in the user's files.
# It is currently limited, and oriented towards detecting comments like this:
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
# get confused by comments that mention "x(n)" in other contexts.
#
# FIXME: develop a systematic convention for these comments.

def infer_real_names(context, ode_var, underscores):
    '''Walk down the list of nodes for the file, looking for comments.
    For every comment, look for any that mention the ode variable.
    Returns a dictionary of translations.
    '''

    # Clever technique found at http://stackoverflow.com/a/1325265/743730
    def valid_id(text, search=re.compile(r'\A[a-zA-Z_][a-zA-Z0-9_]*\Z').search):
        return bool(search(text))

    translations = {}
    comments = [n for n in context.nodes if isinstance(n, Comment)]
    pattern = ode_var.name + r'\((\d+)\)\s+(\S+)'
    for node in comments:
        match = re.search(pattern, node.content)
        if not match:
            continue
        # Found a match.
        index = match.group(1)          # The number inside "x(n)"
        found = match.group(2)          # The rest of the line after "x(n)"
        guess = re.sub(r'(\W+)(\w+)(\W+)', r'\2', found)
        if guess and valid_id(guess):
            our_name = ode_var.name + '_'*underscores + index
            translations[our_name] = guess
    return translations


# -----------------------------------------------------------------------------
# Main translation entry point.
# -----------------------------------------------------------------------------

def create_raterule_model(parse_results, use_species=True, output_format="sbml",
                          name_vars_after_param=False, add_comments=True):

    # First, gather some initial information.
    working_context = first_function_context(parse_results)
    underscores = num_underscores(working_context) + 1
    matlab_func, args = matlab_ode_call(working_context)

    # Next, gather bits from the MATLAB.  Quick summary:
    #  x0 = [num1 num2 ...]           --> "x0" = init_cond_var
    #  [t, y] = ode45(@f, tspan, x0)  --> "y" = assigned_var, "tspan" = time_span
    #  function dy = f(t, x)          --> "x" = dependent_var, "f" = func.name
    #      dy = [row1; row2; ...]     --> "dy" = output_var
    #  end                            -->

    func_var, ode_func = func_from_handle(args[0], working_context, underscores)
    if not ode_func:
        fail(ConversionError,
             'could not extract ODE function from {} call'.format(matlab_func))
    time_span = args[1]
    init_cond_var = args[2]
    assigned_var = assigned_ode_var(matlab_func, working_context)

    # Locate the context object for the ODE function definition.
    function_context = function_declaration(ode_func, working_context, recursive=True)

    # The function form will have to be f(t, y), because that's what Matlab
    # requires.  We want to find out the name of the parameter 'y' in the
    # actual definition, so that we can locate this variable inside the
    # formula within the function.  We don't know what the user will call it,
    # so we have to use the position of the argument in the function def.
    dependent_var = function_context.parameters[1]
    if not isinstance(dependent_var, Identifier):
        fail(ConversionError,
             'failed to parse the arguments to function {}.'.format(ode_func.name))

    # Some people may want to see the species/independent variables named
    # after the input parameter, and others may want it named after the output.
    ode_var = dependent_var if name_vars_after_param else assigned_var

    # Clean up the Matlab (e.g., to remove things that are not relevant) and
    # also rewrite some of the MATLAB to improve our ability to convert it.
    clean_matlab(parse_results, function_context)
    rewrite_matlab(parse_results, output_format)

    # Some users want their variables named based on info they write in
    # comments.  This complicates everything, because we have to rewrite
    # variable names, and we have to infer the name translations.
    translations = infer_real_names(working_context, ode_var, underscores)

    # If we get this far, we are ready to start generating SBML or XPP output.
    document = blank_document(output_format)

    # Find the assignment to the initial condition variable, then create
    # either parameters or species (depending on the run-time selection).
    # The initial value will be the value in the matrix.
    init_cond = working_context.assignments[init_cond_var]
    if not isinstance(init_cond, Array):
        fail(ConversionError,
             'could not find assignment to {}'.format(init_cond_var.name))
    mloop(init_cond,
          lambda idx, item: make_indexed(ode_var, idx, item, translations,
                                         use_species, False, document,
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
    #    y = zeros(4,1);                # assigns whole variable
    #     ...
    #    y(1) = ... something           # assigns location inside the variable
    #    y(2) = ... something
    #    ... etc.
    #
    # To match up the 'y' variables, we rewrite individual y(n) assignments
    # using reconstruct_separate_assignments() to put it all into a common form
    #
    output_var = function_context.returns[0]
    reconstruct_separate_assignments(function_context, output_var)
    var_def = function_context.assignments[output_var]
    if not isinstance(var_def, Array):
        fail(ConversionError,
             'failed to parse body of function {}'.format(function_context.name))
    # The number of items in the output var must match initial conditions var.
    # Ignore if one is a column vector and the other a row vector.
    if vector_length(init_cond) != vector_length(var_def):
        fail(ConversionError,
             'initial conditions array and output array have different sizes')
    mloop(var_def,
          lambda idx, item: make_rate_rule(ode_var, dependent_var, translations,
                                           idx, item, document, underscores,
                                           function_context))

    # Create remaining parameters.  Break up matrix assignments by looking up
    # the value assigned to the variable; if it's a matrix value, then the
    # variable is turned into parameters named foo_1, foo_2, etc.  Also, we
    # have to decide what to do about duplicate variable names showing up
    # inside the function body and outside.  The approach here is to have
    # variables inside the function shadow ones outside.  FIXME: check if
    # something more complicated is going on in the Matlab code.
    #
    skip_vars = [init_cond_var, output_var, assigned_var, ode_var, func_var]
    if isinstance(time_span, Identifier):
        # If the time span is a named variable and not an array, skip it too.
        skip_vars.append(time_span)
    make_remaining_vars(working_context, function_context, skip_vars,
                        translations, document, underscores)

    # Deal with final quirks.
    if ref_name('time', working_context) or ref_name('time', function_context):
        # XPP assumes 't' is time, so we only need to handle it for SBML.
        if output_format == 'sbml':
            create_assigned_parameter(document, 't', 'time', True)
        elif output_format == "biocham":
            # Although we don't need to define 't' for XPP, we will need to add
            # (in poss-processing) a definition to the SBML produced by Biocham.
            document.post_add.append(('t', 'time'))

    # Finally, return the model, with extra info about things that may need
    # to be added back in post-processing if we are hand this to BIOCHAM.
    output = generate_output(document, add_comments)
    post_add = None if output_format == 'sbml' else document.post_add
    post_convert = None if output_format == 'sbml' else document.post_convert
    return [output, post_add, post_convert]


def is_vector(matrix):
    '''Returns True if "matrix" is a single row vector.'''
    return (len(matrix.rows) == 1 and len(matrix.rows[0]) >= 1)


def vector_length(matrix):
    '''Returns the length of the row or column vector in "matrix".'''
    return len(matrix.rows[0]) if is_vector(matrix) else len(matrix.rows)


def mloop(matrix, func):
    # Calls function 'func' on a row or column of values from the matrix.
    # Note: the argument 'i' is 0-based, not 1-based like Matlab vectors.
    # FIXME: this only handles 1-D row or column vectors.
    base = matrix.rows
    if is_vector(matrix):
        for i in range(0, vector_length(matrix)):
            entry = base[0][i]
            func(i, entry)
    else:
        for i in range(0, vector_length(matrix)):
            entry = base[i][0]
            func(i, entry)


def make_indexed(var, index, content, translations, use_species, use_rules,
                 document, underscores, context):
    # Helper function:
    def make_declaration(the_name, the_value, const=(not use_rules)):
        if use_species:
            create_species(document, the_name, the_value, False)
        else:
            create_parameter(document, the_name, the_value, const)

    name = rename(var.name, str(index + 1), underscores)
    real_name = translations[name] if name in translations else name
    if isinstance(content, Number):
        # The value is a number => it can be the SBML 'value' attribute.
        make_declaration(real_name, content.value)
    elif constant_expression(content, context):
        # If the RHS is an expression but it's all constant values, we turn it
        # into an initial assignment.
        make_declaration(real_name, 0, False)
        formula = MatlabGrammar.make_formula(content)
        create_initial_assignment(document, real_name, formula)
    else:
        # Not a simple number => may depend on quantities that change during
        # simulation.  Create assignment rule or initial assignment.
        translator = lambda node: munge_reference(node, context, underscores)
        formula = MatlabGrammar.make_formula(content, atrans=translator)
        if not formula:
            fail(ConversionError,
                 'Failed to convert formula for {}'.format(var))
        make_declaration(real_name, 0, False)
        create_assignment(document, real_name, formula, use_rules)


def make_rate_rule(assigned_var, dep_var, translations, index, content,
                  document, underscores, context):
    # Currently, this assumes there's only one math expression per row or
    # column, meaning, one subscript value per row or column.
    translator = lambda node: munge_reference(node, context, underscores)
    string_formula = MatlabGrammar.make_formula(content, atrans=translator)
    if not string_formula:
        fail(ConversionError,
             'Failed to convert formula for row {}'.format(index + 1))

    # We need to rewrite matrix references "x(n)" to the form "x_n", and
    # rename the variable to the name used for the results assignment
    # in the call to the ode* function.
    xnameregexp = dep_var.name + '_'*underscores + r'(\d+)'
    newnametransform = assigned_var.name + '_'*underscores + r'\1'
    formula = re.sub(xnameregexp, newnametransform, string_formula)

    # Finally, write the rate rule.
    rule_var = rename(assigned_var.name, str(index + 1), underscores)
    if rule_var in translations:
        rule_var = translations[rule_var]
    formula = translate_names(formula, translations)
    create_rate_rule(document, rule_var, formula)


# FIXME only handles 1-D matrices.
# FIXME grungy part for looking up identifier -- clean up & handle more depth

def munge_reference(array, context, underscores):
    if not isinstance(array.name, Identifier):
        return MatlabGrammar.make_formula(array)
    if not array.args:
        # Nothing to do. Can happen it's Ambiguous with no args => identifier.
        return array.name.name
    # Base name starts with one less underscore because the loop process
    # adds one in front of each number.
    name = array.name.name
    constructed = name + '_'*(underscores - 1)
    assignments = all_assignments(context)
    for i in range(0, len(array.args)):
        element = array.args[i]
        i += 1
        if isinstance(element, Number):
            constructed += '_' + element.value
        elif isinstance(element, Identifier):
            # The subscript is not a number.  If it's a simple variable and
            # we've seen its value, we can handle it by looking up its value.
            var_name = element.name
            if var_name not in assignments:
                fail(UnsupportedInputError, 'Unable to handle "' + name + '"')
            assigned_value = assignments[var_name]
            if isinstance(assigned_value, Number):
                constructed += '_' + assigned_value
            else:
                fail(UnsupportedInputError, 'Unable to handle "' + name + '"')
    return constructed


def make_remaining_vars(working_context, function_context, skip_vars,
                          name_translations, document, underscores):

    all_vars = dict(itertools.chain(working_context.assignments.items(),
                                    function_context.assignments.items()))
    all_vars = {lhs:rhs for lhs, rhs in all_vars.items() if lhs not in skip_vars}

    # We do it slightly differently if the variable is assigned inside the
    # ODE function versus outside.  Inside, we make them assignment rules
    # because the values would normally be recomputed every time the function
    # is called.  Outside, we make them one-time initial assignments.
    for var, rhs in natsorted(all_vars.items(), alg=ns.IGNORECASE):
        in_function = True if var in function_context.assignments else False
        if isinstance(rhs, Number):
            create_parameter(document, var.name, rhs.value, True)
        elif isinstance(var, Array) or isinstance(var, ArrayRef):
            if isinstance(rhs, FunCall) and rhs.name.name.startswith('ode'):
                continue
            else:
                # FIXME: it may be possible to handle some cases like this.
                text = MatlabGrammar.make_formula(var)
                fail(ConversionError,
                     'unable to convert array assignment {}'.format(text))
        elif isinstance(rhs, Array):
            mloop(rhs,
                  lambda idx, item: make_indexed(var, idx, item, name_translations,
                                                 False, in_function, document,
                                                 underscores, function_context))
        elif isinstance(rhs, Handle):
            # Skip function handles. If any was used in the ode* call, it will
            # have been dealt with earlier.
            continue
        elif isinstance(rhs, Expression):
            # Catches the remaining forms of RHSs we care about, including
            # when the value is another variable, i.e., "x = y".  First we
            # see if the RHS is a constant expression, because then it can be
            # made an initial assignment instead of an assignment rule.
            if constant_expression(rhs, context):
                create_parameter(document, var.name, 0, True)
                formula = MatlabGrammar.make_formula(rhs)
                create_initial_assignment(document, var.name, formula)
            else:
                translator = lambda node: munge_reference(node, function_context,
                                                          underscores)
                formula = MatlabGrammar.make_formula(rhs, atrans=translator)
                translated = translate_names(formula, name_translations)
                create_assigned_parameter(document, var.name, translated,
                                          in_function)


def reconstruct_separate_assignments(context, var):
    # Look through the context for assignments to an ArrayRef whose name is
    # equal to the name of "var".  Construct an Array instead of an ArrayRef,
    # with the rows of the array corresponding to the values in the separate
    # assignments.  Replace the separate assignments in "context" with a
    # single assignment with "var" as the LHS and the Array as the RHS.
    need_adjust = []
    for assigned in context.assignments.keys():
        if not isinstance(assigned, ArrayRef):
            continue
        if assigned.name.name.startswith(var.name):
            need_adjust.append(assigned)
    if need_adjust:
        # Build a new array.  FIXME this assumes a 1-D array!
        rows = [None]*len(need_adjust)
        for elem in need_adjust:
            # Matlab arrays are 1-indexed, Python are 0-indexed.
            index = int(elem.args[0].value) - 1
            rows[index] = context.assignments[elem]
            context.assignments.pop(elem)
        context.assignments[var] = Array(is_cell=False, rows=[rows])
        return context.assignments[var]
    else:
        return var


def generate_output(document, add_comments):
    if isinstance(document, XPPDocument):
        return generate_xpp_string(document, add_comments)
    else:
        writer = SBMLWriter();
        if add_comments:
            writer.setProgramName("MOCCASIN")
            writer.setProgramVersion(__version__)
        return writer.writeSBMLToString(document);


def translate_names(text, translations):
    for oldname, newname in translations.items():
        text = text.replace(oldname, newname)
    return text


def rename(base, tail='', num_underscores=1):
    return ''.join([base, '_'*num_underscores, tail])



# -----------------------------------------------------------------------------
# Post-processing output from BIOCHAM web service.
# -----------------------------------------------------------------------------

def process_biocham_output(sbml, parse_results, post_add, post_convert,
                           add_comments=True):
    # 'post_add' contains a list of tuples (var, ast) to add as SBML
    # assignment rules into the output.
    #
    # 'post_convert' is a list of tuples (var, ast) of variables to convert
    # to assignment rules.  It's assumed that they are already in the input,
    # but as initial assignments instead of assignment rules.
    if not sbml:
        return sbml

    # python 3 changed the way temporary files read/wrote data
    # and used bytes that need to encoded/decoded
    try:
        document = SBMLReader().readSBMLFromString(sbml)
    except:
        document = SBMLReader().readSBMLFromString(sbml.decode())

    if not document:
        return sbml
    model = document.getModel()
    if not model:
        return sbml

    # First add possibly-missing pieces, so that the conversion step below
    # won't fail due to something like a missing definition for 't'.
    for var, formula in post_add:
        create_sbml_parameter(model, var, 0, const=False)
        create_sbml_assignment_rule(model, var, parseL3Formula(formula))

    # Convert Biocham's L2v2 model to L3v1.
    success = document.setLevelAndVersion(3, 1, False)
    if not success:
        # FIXME provide more info about what happened.
        fail(ConversionError, 'failed to convert output from Biocham.')

    # Convert constructs if necessary.
    for var, formula in post_convert:
        model.removeRule(var)
        model.removeParameter(var)
        create_sbml_parameter(model, var, 0, const=True)
        create_sbml_initial_assignment(model, var, parseL3Formula(formula))

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

    # Set the model id & name.
    if parse_results.functions and parse_results.name:
        id = parse_results.functions[parse_results.name].name.name
        model.setId(id)
        model.setName(id + ' translated by MOCCASIN')

    # Sort the parameters, for easier reading.
    sort_sbml_parameters(document.getModel())

    # Set up to write the output.
    writer = SBMLWriter();
    if add_comments:
        writer.setProgramName("MOCCASIN")
        writer.setProgramVersion(__version__)

    # Write it, and we are done!  Pop the champagne cork.
    return writer.writeSBMLToString(document)


# -----------------------------------------------------------------------------
# Miscellaneous utilities.
# -----------------------------------------------------------------------------

def valid_file(file):
    return os.path.exists(file) and os.path.isfile(file)


def expanded_path(path):
    if path: return os.path.expanduser(os.path.expandvars(path))
    else:    return None


def fail(ex, arg):
    raise ex(arg)


# -----------------------------------------------------------------------------
# Command line interface (for testing and debugging).
# -----------------------------------------------------------------------------

def parse_args(argv):
    help_msg = 'MOCCASIN version ' + __version__ + '\n' + main.__doc__
    try:
        options, path = getopt.getopt(argv[1:], "cdpqxoOrvl")
    except:
        raise SystemExit(help_msg)
    if len(path) != 1 or len(options) > 8:
        raise SystemExit(help_msg)
    add_comments     = not any(['-c' in y for y in options])
    debug            = any(['-d' in y for y in options])
    quiet            = any(['-q' in y for y in options])
    print_parse      = any(['-x' in y for y in options])
    print_raw        = any(['-r' in y for y in options])
    use_species      = not any(['-p' in y for y in options])
    name_after_param = any(['-l' in y for y in options])
    create_xpp       = any(['-o' in y for y in options])
    create_biocham   = any(['-O' in y for y in options])
    if not create_xpp and not create_biocham:
        output_format = "sbml"
    elif create_xpp:
        output_format = "xpp"
    else:
        output_format = "biocham"
    return path[0], debug, quiet, print_parse, print_raw, use_species, \
        name_after_param, output_format, add_comments


def main(argv):
    """Usage: converter.py [options] FILENAME.m

Converts an ODE MATLAB model in FILENAME.m into an ODE-oriented SBML or XPP
model.  Available options:
 -c   Omit comments in the SBML file about program version and other info
 -d   Drop into pdb before starting to parse the MATLAB input
 -h   Print this help message and quit
 -l   Name variables per ODE function's parameters (default: use output variable)
 -o   Convert to XPP .ode file format (default: produce SBML)
 -O   Convert to XPP .ode file format suitable for use with BIOCHAM
 -p   Turn variables into SBML parameters (default: make them SBML species)
 -q   Be quiet; just produce the final output, nothing else
 -r   Print the raw MatlabNode output for the output printed with option -x
 -x   Print extra debugging info about the interpreted MATLAB
"""
    (path, debug, quiet, print_parse, print_raw, use_species, name_after_param,
     output_format, add_comments) = parse_args(argv)

    # Try to read the file contents.
    path = expanded_path(path)
    if not valid_file(path):
        fail(FileError, 'Not a file: "{}"'.format(path))
    try:
        file = open(path, 'r')
        file_contents = file.read()
    except Exception as err:
        fail(FileError, 'Unable to open "{}": {}'.format(path, err))
    finally:
        file.close()

    if not quiet:
        if output_format == "biocham":
            output_type = "XPP for BIOCHAM"
        elif output_format == "xpp":
            output_type = "XPP"
        else:
            output_type = "SBML"
        print('----- {} file '.format(output_type) + path + ' ' + '-'*30)
        print(file_contents)
    if debug:
        pdb.set_trace()

    # Parse the SBML contents and do initial minimal sanity checking.
    parse_results = parse_matlab(path)
    sanity_check_matlab(parse_results)

    # Now do the actual conversion.
    NameGenerator().reset()
    [out, _, _] = create_raterule_model(parse_results, use_species, output_format,
                                        name_after_param, add_comments)

    # Print the conversion results and other things.
    if print_parse and not quiet:
        print('\n----- interpreted output ' + '-'*50)
        parser.print_parse_results(parse_results, print_raw)
    if not quiet:
        print('\n----- {} output '.format(output_type) + '-'*50)
    print(out)


if __name__ == '__main__':
    main(sys.argv)
