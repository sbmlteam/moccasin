#!/usr/bin/env python

import glob, sys
from pyparsing import ParseException, ParseResults
sys.path.append('..')
sys.path.append('../../utilities')

from matlab_parser import *
from libsbml import *


def parse_file(path):
    file = open(path, 'r')
    try:
        (contexts, raw_results) = parse_matlab_string(file)
    except ParseException as err:
        print("error: {0}".format(err))


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


def create_model():
    # Create model structure
    model = document.createModel()
    check(model, 'create model')

    # Create default compartment
    c1 = model.createCompartment()
    check(c1,                                 'create compartment')
    check(c1.setId('c1'),                     'set compartment id')
    check(c1.setConstant(True),               'set compartment "constant"')
    check(c1.setSize(1),                      'set compartment "size"')
    check(c1.setSpatialDimensions(3),         'set compartment dimensions')

    # Create parameters

    # Create rate rules

    # Write the Model
    print writeSBMLToString(document)
