#!/usr/bin/env python

import sys, pytest

sys.path.append('..')
from trivial_parser import parse_string

def test_02():
    assert parse_string("x = 123") == "x"
    assert parse_string("x = 123 % comment") == "x"
    assert parse_string("a = 'foo''s party'") == "a"
