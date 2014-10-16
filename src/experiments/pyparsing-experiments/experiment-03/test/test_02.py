#!/usr/bin/env python

import sys, pytest

sys.path.append('..')
from trivial_parser import parse_string

def test_02():
    assert parse_string("x = 123") == {'x': '123'}
    assert parse_string("x = 123 % comment") == {'x': '123 % comment'}
    assert parse_string("a = 'foo''s party'") == {'a': "'foo''s party'", 'x': '123 % comment'}
