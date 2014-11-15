#!/usr/bin/env python

import sys
import getopt
from grammar import *


def get_filename_and_options(argv):
    try:
        options, path = getopt.getopt(argv[1:], "dp")
    except:
        raise SystemExit(main.__doc__)
    if len(path) != 1 or len(options) > 2:
        raise SystemExit(main.__doc__)
    debug = any(['-d' in y for y in options])
    do_print = any(['-p' in y for y in options])
    return path[0], debug, do_print


def main(argv):
    '''Usage: matlab_parser.py [-p] [-d] FILENAME.m
Arguments:
  -p   (Optional) Print a representation of the interpreted input
  -d   (Optional) Drop into pdb as the final step
'''

    path, debug, print_interpreted = get_filename_and_options(argv)

    file = open(path, 'r')
    print '----- file ' + path + ' ' + '-'*30
    contents = file.read()
    print contents

    print '----- raw parse results ' + '-'*50
    parser  = MatlabGrammar()
    results = parser.parse_string(contents, True)
    print ''

    if print_interpreted:
        print '----- interpreted output ' + '-'*50
        parser.print_parse_results(results)

    if debug:
        pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)
