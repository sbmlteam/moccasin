#!/usr/bin/env python

from __future__ import print_function
import glob
import sys
from pyparsing import ParseException, ParseResults
sys.path.append('../../moccasin/converter/')
sys.path.append('../../moccasin/')
from matlab_parser import *
from converter import *

sys.setrecursionlimit(10000)

def main(argv):

    #Flag values used for testing
    debug=False
    quiet=False
    print_parse=True
    use_species=True
    output_sbml=True
    additional = ''
    
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
            parser = MatlabGrammar()
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

        [sbml, additional] = create_raterule_model(parse_results,
                                                   use_species,
                                                   output_sbml,
                                                   use_func_param_for_var_name=False,
                                                   add_comments=False)
        print(sbml)

        print(additional)


if __name__ == '__main__':
    main(sys.argv)
