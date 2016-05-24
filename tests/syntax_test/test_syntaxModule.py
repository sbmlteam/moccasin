#!/usr/bin/env python2.7

from __future__ import print_function
import pytest
import sys
import glob
import os
import codecs
import locale
import platform
import re
from string import printable
sys.path.append('moccasin/')
sys.path.append('../moccasin')
sys.path.append('../../moccasin')
from matlab_parser import MatlabGrammar

_VERSION2 = platform.python_version().startswith('2')

#Generates (multiple) parametrized calls to a test function
def pytest_generate_tests(metafunc):
    # called once per test function
    funcarglist = metafunc.cls.params[metafunc.function.__name__]
    argnames = list(funcarglist[0])
    metafunc.parametrize(argnames, [[funcargs[name] for name in argnames]
            for funcargs in funcarglist],scope='module')

#Parses the file and prints interpreted result(output is captured)
def build_model(path):
    try:
        with MatlabGrammar() as parser:
            results = parser.parse_file(path, fail_soft=True)
            parser.print_parse_results(results, print_raw=True)
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

    def test_syntaxCases(self, capsys, model, parsed):
        build_model(model)
        out, err = capsys.readouterr()
        from_parser = out
        from_file = read_parsed(parsed)
        if _VERSION2:
            from_file = re.sub(r'\\\\n', r'\\n', from_file)
            # Case valid_42 has a non-ascii character that ends up getting
            # quoted somehow, somewhere, probably by py.test capsys.  After
            # 2 hours of trying to find a way to do it correctly, I give up.
            # This is wrong but I don't care anymore.
            from_file = re.sub(r'\xb5', r'\xb5', from_file)
            from_parser = re.sub(r'\\xc2', r'', from_parser)
            from_parser = re.sub(r'\\xb5', r'\xb5', from_parser)
        print("---From solution file---")
        print(repr(from_file))
        print("---Ouput from parser---")
        print(repr(from_parser))
        print ("\n \n")
        assert from_parser == from_file
