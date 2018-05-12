#!/usr/bin/env python

from __future__ import print_function
import glob
import sys
from pyparsing import ParseException, ParseResults
sys.path.append('../..')
from moccasin import *

sys.setrecursionlimit(10000)

def main(argv):

    #Flag values used for testing
    debug=False
    quiet=False
    print_parse=True

    for path in glob.glob("converter-test-cases/valid*.m"):
        file = open(path, 'r')
        file_contents = file.read()
        file.close()

        if not quiet:
            print('----- file ' + path + ' ' + '-'*30)
            print(file_contents)

        if debug:
            pdb.set_trace()
        try:
            with MatlabParser() as parser:
                parse_results = parser.parse_string(file_contents)
        except ParseException as err:
            print("error: {0}".format(err))

        if print_parse and not quiet:
            print('')
            print('----- interpreted output ' + '-'*50)
            parser.print_parse_results(parse_results)

        if not quiet:
            print('')
            print('----- SBML output ' + '-'*50)

        [sbml, _, _] = create_raterule_model(parse_results,
                                             use_species=True,
                                             output_format="sbml",
                                             name_vars_after_param=False,
                                             add_comments=False)
        print(sbml)


if __name__ == '__main__':
    main(sys.argv)
