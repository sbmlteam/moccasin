#!/usr/bin/env python

import sys, pytest

sys.path.append('..')
from trivial_parser import parse_string

def test_01():
    assert parse_string("'foo'") == "foo"
    assert parse_string("'foo bar'") == "foo bar"
    assert parse_string("'foo''bar'") == "foo'bar"
    assert parse_string("'this is a ''quoted'' string'") == "this is a 'quoted' string"
