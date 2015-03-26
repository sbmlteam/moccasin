#!/usr/bin/env python

from __future__ import print_function
import pytest
import sys
import glob
import os
from pyparsing import ParseResults
sys.path.append('moccasin/')
sys.path.append('../moccasin')
sys.path.append('../../moccasin')
from evaluate_formula import *
from string import printable
import codecs

#Generates (multiple) parametrized calls to a test function
def pytest_generate_tests(metafunc):
    # called once per test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = list(funcarglist[0])
    metafunc.parametrize(argnames, [[funcargs[name] for name in argnames]
            for funcargs in funcarglist],scope='module')

#Parses the file and prints interpreted result(output is captured)                       
def build_model(path):
    file = open(path,'r')
    contents = file.read()
    try:
        results = ''
        formula_parser = NumericStringParser()
        formula = contents
        if formula is not None and formula != '':
            results = formula_parser.eval(formula)
        file.close()
        print(results)
    except Exception as e:
        print(e)

#reads file containing expected parsed model and returns it as string
def read_parsed(path):
    file = codecs.open(path, encoding='utf-8') 
    contents = file.read()
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
    txt_path = path + ['valid_*.txt']
    matlab_models = glob.glob(os.path.join(*m_path))
    parsed_models = glob.glob(os.path.join(*txt_path))
    pairs = list()
    for i in range(len(matlab_models)):
        pairs.append((dict(model = matlab_models[i], parsed = parsed_models[i])))
    parameters = {'test_evaluateCases' : pairs}
    return parameters

class TestClass:
    # a map specifying multiple argument sets for a test method
    params = obtain_params()
    
    def test_evaluateCases(self,capsys, model, parsed):
        build_model(model)
        out,err=capsys.readouterr()
        output=out.replace('\n', '').replace('\r', '')
        test_parsed=read_parsed(parsed).replace('\n', '').replace('\r', '')
        print("---From solution file---")
        print(repr(test_parsed))
        print("---Ouput from parser---")
        print(repr(output))
        print ("\n \n")
        assert output==test_parsed

