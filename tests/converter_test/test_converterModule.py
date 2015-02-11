#!/usr/bin/env python

import pytest
import sys
from pyparsing import ParseResults
sys.path.append('../../moccasin/converter/')
sys.path.append('../../moccasin/')
from matlab_parser import *
from converter import *
    
def build_model(path):
    file = open(path,'r')
    contents = file.read()
    parser = MatlabGrammar()
    results = parser.parse_string(contents, fail_soft=True)
    sbml = create_raterule_model(results, True)
    file.close()
    print(sbml)

def read_sbml (path):
    file = open(path,'r')
    contents = file.read()
    file.close()
    return contents
            
def test_case51(capsys):
    build_model("converter-test-cases/valid_51.m")
    out,err=capsys.readouterr()
    assert out.strip()== read_sbml("converter-test-cases/valid_51.xml").strip()

def test_case52(capsys):
    build_model("converter-test-cases/valid_52.m")
    out,err=capsys.readouterr()
    assert out.strip()== read_sbml("converter-test-cases/valid_52.xml").strip()

def test_case53(capsys):
    build_model("converter-test-cases/valid_53.m")
    out,err=capsys.readouterr()
    assert out.strip()== read_sbml("converter-test-cases/valid_53.xml").strip()

def test_case54(capsys):
    build_model("converter-test-cases/valid_54.m")
    out,err=capsys.readouterr()
    assert out.strip()== read_sbml("converter-test-cases/valid_54.xml").strip()

#def test_case55(capsys):
#    build_model("converter-test-cases/valid_55.m")
#    out,err=capsys.readouterr()
#    assert out.strip()== read_sbml("converter-test-cases/valid_55.xml").strip()
