#!/usr/bin/env python

import glob
import sys
from pyparsing import ParseException, ParseResults
sys.path.append('..')
sys.path.append('../../parser')
from matlab import *
from converter import *


def main(argv):
    '''Usage: run-syntax-tests.py [-d] [-v]
Arguments:
  -n  (Optional) Don't drop into pdb upon a parsing exception -- keep going.
  -p  (Optional) Print annotated Matlab parsing results.
  -s  (Optional) Turn variables into species (default: make them parameters)
'''

    try:
        options = getopt.getopt(argv[1:], "nps")
    except:
        raise SystemExit(main.__doc__)

    do_debug        = not any(['-n' in y for y in options])
    use_species     = any(['-s' in y for y in options])
    do_print_interp = any(['-p' in y for y in options])

    parser = MatlabGrammar()

    for f in glob.glob("converter-test-cases/valid*.m"):
        print('===== ' + f + ' ' + '='*30)
        with open(f, 'r') as file:
            contents = file.read()
        print(contents.rstrip())
        try:
            results = parser.parse_string(contents, fail_soft=True)
            if do_print_interp:
                print('----- interpreted ' + '-'*30)
                parser.print_parse_results(results)
                print('')
            print('----- SBML output ' + '-'*30)
            sbml = create_raterule_model(results)
            print sbml
        except Exception as err:
            if do_debug and not results:
                print('Object "results" contains the output of parse_string()')
                pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)
