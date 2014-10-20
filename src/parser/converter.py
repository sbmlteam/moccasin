#!/usr/bin/env python

import glob, sys, pdb, re
from pyparsing import ParseException, ParseResults
sys.path.append('..')
sys.path.append('../../utilities')

from matlab_parser import *
from libsbml import *


# -----------------------------------------------------------------------------
# Parsing-related stuff.
# -----------------------------------------------------------------------------

# We turn simple assignments in the outer portion of the file into global
# parameters in the SBML model.

def get_all_variables(mparse):
    # Look for the default context
    default_context = None
    for context in mparse:
        if context['name'] == '(default context)':
            default_context = context
            break
    if default_context == None:
        return None
    if len(default_context['variables']) == 0:
        return None

    # Loop through the variables and create a dictionary to return.
    parameters = {}
    for id, value in default_context['variables'].items():
        # If the variable is an array, we split it by rows.
        if len(value[0]) > 1:
            i = 1
            for row in value[0]:
                new_id = id + "_" + str(i)
                parameters[new_id] = translate_parsed_formula(row)
                i += 1
        else:
            parameters[id] = translate_parsed_formula(value)
    return parameters


def get_all_function_calls(mparse):
    calls = {}
    for context in mparse:
        if len(context['calls']) == 0:
            continue
        for fname, rhs in context['calls'].items():
            calls[fname] = rhs
    return calls


def get_function_declaration(name, context):
    if len(context['functions']) == 0:
        return None
    if name in context['functions']:
        return context['functions'].get(name)
    return None


def get_variable(name, context):
    if name in context['variables']:
        return context['variables'].get(name)
    return None


def find_function(fname, mparse):
    for context in mparse:
        if context['name'] == fname:
            return context


def matrix_rows_as_list(pr):
    result = []
    for row in pr[0]:
        pr_formula = row[0][0]
        result.append(translate_parsed_formula(pr_formula))
    return result


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
    if value == None:
        print('LibSBML returned a null value trying to ' + message + '.')
        print('Exiting.')
        sys.exit(1)
    elif type(value) is int:
        if value == LIBSBML_OPERATION_SUCCESS:
            return
        else:
            print('Error encountered trying to ' + message + '.')
            print('LibSBML returned error code ' + str(value) + ': "' \
                  + OperationReturnValue_toString(value).strip() + '"')
            print('Exiting.')
            sys.exit(1)
    else:
        return


def create_model(mparse):
    # Create model structure
    try:
        document = SBMLDocument(3, 1)
    except ValueError:
        print('Could not create SBMLDocumention object')
        sys.exit(1)
    model = document.createModel()
    check(model, 'create model')

    # Create default compartment
    c = model.createCompartment()
    check(c,                              'create compartment')
    check(c.setId('comp1'),               'set compartment id')
    check(c.setConstant(True),            'set compartment "constant"')
    check(c.setSize(1),                   'set compartment "size"')
    check(c.setSpatialDimensions(3),      'set compartment dimensions')

    # Pull out the ODE function information and create rate rules.
    # We need this because we'll do some translation on var names later.

    # FIXME massive assumptions on the structure here. This is just a start.

    calls = get_all_function_calls(mparse)
    handle = None
    for name, rhs in calls.items():
        if name.startswith('ode'):
            # Look up the function it calls inside its body.
            called_function = search_for('function handle', rhs)
            invocation = rhs
            break
    if called_function:
        fname = called_function[0][1]
        declaration = get_function_declaration(fname, contexts[0])

        outer_xname = invocation[-1][0]

        output_var  = declaration['output'][0] # FIXME might have more than one
        input_vars  = declaration['args']
        inner_xname = input_vars[-1]

        context = find_function(fname, mparse)
        if context:
            # We found a function definition matching the name of what's called
            # by the ode function.  In this simple version of the converter, we
            # only look for a variable of the same name as the one being
            # returned by this function.  This variable will be a vector.
            # We take apart the vector, using each row as an ODE definition.
            var_def = get_variable(output_var, context)
            rows = matrix_rows_as_list(var_def)
            i = 1
            for row in rows:
                rule_var = output_var + "_" + str(i)

                # Minor hiccup: the row formulas will contain array variable
                # references, corresponding to the input var.
                xnameregexp = inner_xname + r'\((\d+)\)'
                newnametranform = outer_xname + r'_\1'
                formula = re.sub(xnameregexp, newnametranform, row)

                i += 1
                r = model.createRateRule()
                check(r,                       'create rate rule')
                check(r.setVariable(rule_var), 'set rule variable')
                check(r.setFormula(formula),   'set rule formula')

                # We also have to create the output variables.
                p = model.createParameter()
                check(p.setId(rule_var),        'set parameter id')
                check(p.setConstant(False),    'set parameter "constant"')
                check(p.setValue(0),           'set parameter value')


    # Create remaining parameters
    parameters = get_all_variables(mparse)
    if parameters is not None:
        for id, math in parameters.iteritems():
            p = model.createParameter()
            check(p,                           'create parameter')
            check(p.setId(id),                 'set parameter id')
            check(p.setConstant(True),         'set parameter "constant"')

            ast = parseL3Formula(math)
            if ast is not None:
                ia = model.createInitialAssignment()
            check(ia,                          'create initial assignment')
            check(ia.setMath(ast),             'set initial assignment formula')
            check(ia.setSymbol(id),            'set initial assignment symbol')


    # Write the Model
    return writeSBMLToString(document)


#
# Driver
#

if __name__ == '__main__':
    debug = False
    echo_raw_parse = False
    path = None

    if len(sys.argv) < 2:
        print("Must be given at least one argument: the file to convert")
        sys.exit(1)

    for arg in sys.argv[1:]:
        if arg == '-d':
            debug = True
        elif arg == '-p':
            echo_raw_parse = True
        else:
            path = arg

    file = open(path, 'r')

    print('----- file ' + path + ' ' + '-'*30)
    file_contents = file.read()
    print(file_contents)

    if debug:
        pdb.set_trace()
    try:
        if echo_raw_parse:
            print('')
            print('----- interpreted output ' + '-'*50)

        mparse = parse_matlab_string(file_contents, echo_raw_parse)

        print('')
        print('----- SBML output ' + '-'*50)
        sbml = create_model(mparse)
    except ParseException as err:
        print("error: {0}".format(err))
    print sbml
