#!/usr/bin/env python

from __future__ import print_function
import pytest
import sys
import glob
import os
import codecs
import platform
from string import printable
sys.path.append('moccasin/')
sys.path.append('../moccasin')
sys.path.append('../../moccasin')
from matlab_parser import MatlabGrammar

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
        with MatlabGrammar() as parser:
            results = parser.parse_string(contents, fail_soft=True)
            parser.print_parse_results(results, print_raw=True)
    except Exception as e:
        print(e)
    finally:
        file.close()

#reads file containing expected parsed model and returns it as string
def read_parsed(path):
    file = codecs.open(path, encoding='utf-8') 
    contents = file.read()
    file.close()
    return contents

# Constructs the params dictionary for test function parametrization
def obtain_params():
    if os.path.isdir('tests'):
        path = ['tests', 'syntax_test', 'syntax-test-cases']
    elif os.path.isdir('syntax_test'):
        path = ['syntax_test', 'syntax-test-cases']
    elif os.path.isdir('syntax-test-cases'):
        path = ['syntax-test-cases']
    m_path = path + ['valid*.m']
    matlab_models = glob.glob(os.path.join(*m_path))
    parsed_models = [x.rsplit('.')[0] + '.txt' for x in matlab_models]
    pairs = list()
    for i in range(len(matlab_models)):
        pairs.append((dict(model = matlab_models[i], parsed = parsed_models[i])))
    parameters = {'test_syntaxCases' : pairs}
    return parameters

class TestClass:
    # a map specifying multiple argument sets for a test method
    params = obtain_params()
    version2 = platform.python_version().startswith('2')

    def test_syntaxCases(self, capsys, model, parsed):
        build_model(model)
        out, err = capsys.readouterr()
#        2016-05-23 <mhucka@caltech.edu> taking this out, because i'm having
#        trouble with Travis-based tests on GitHub and this may be the cause.
#
#        output = out.replace('\n', '').replace('\r', '')
#        test_parsed = read_parsed(parsed).replace('\n', '').replace('\r', '')
        output = out
        if self.version2:
            output = output.decode('unicode_escape')
        test_parsed = read_parsed(parsed)
        print("---From solution file---")
        print(repr(test_parsed))
        print("---Ouput from parser---")
        print(repr(output))
        print ("\n \n")
        assert output == test_parsed
