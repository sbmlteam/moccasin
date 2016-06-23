#!/usr/bin/env python

from __future__ import print_function
import sys
sys.path.append('moccasin/converter/')
sys.path.append('../moccasin/converter/')
sys.path.append('../../moccasin/converter/')
sys.path.append('moccasin/')
sys.path.append('../moccasin')
sys.path.append('../../moccasin')

import codecs
from evaluate_formula import *
import getopt
import glob
import os
from pyparsing import ParseResults
import pytest
from string import printable


# Generates (multiple) parametrized calls to a test function
def pytest_generate_tests(metafunc):
    # called once per test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = list(funcarglist[0])
    metafunc.parametrize(argnames, [[funcargs[name] for name in argnames]
            for funcargs in funcarglist],scope='module')

# Parses the file and prints interpreted result(output is captured)
def parse_matlab_file(path):
    file = open(path,'r')
    contents = file.read()
    try:
        results = ''
        formula_parser = NumericStringParser()
        formula = contents
        if formula is not None and formula != '':
            return formula_parser.eval(formula)
    except Exception as e:
        print(e)
    finally:
        file.close()

#reads file containing expected parsed model and returns it as string
def read_parsed(path):
    file = codecs.open(path, encoding='utf-8') 
    contents = ''.join(file.readlines())
    file.close()
    return contents

# Constructs the params dictionary for test function parametrization
def obtain_params():
    if os.path.isdir('tests'):
        path = ['tests', 'evaluate_test', 'evaluate-test-cases']
    elif os.path.isdir('evaluate_test'):
        path = ['evaluate_test', 'evaluate-test-cases']
    elif os.path.isdir('evaluate-test-cases'):
        path = ['evaluate-test-cases']
    m_path = path + ['valid_*.m']
    input_files = glob.glob(os.path.join(*m_path))
    output_files = [x.rsplit('.')[0] + '.txt' for x in input_files]
    pairs = list()
    for i in range(len(input_files)):
        pairs.append((dict(input = input_files[i], expected = output_files[i])))
    parameters = {'test_evaluateCases' : pairs}
    return parameters

class TestClass:
    # A map specifying multiple argument sets for a test method
    params = obtain_params()

    def test_evaluateCases(self, capsys, input, expected):
        expected_output = read_parsed(expected).replace('\n', '').replace('\r', '')
        getcontext().prec = 12
        actual_output = parse_matlab_file(input)
        print("--- From solution file ---")
        print(expected_output)
        print("--- Ouput from parser ---")
        print(actual_output)
        print ("\n \n")
        assert actual_output == Decimal(expected_output)
