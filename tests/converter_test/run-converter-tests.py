#!/usr/bin/env python

from __future__ import print_function
import glob
import sys
import getopt
from pyparsing import ParseException, ParseResults
sys.path.append('../../moccasin/converter/')
sys.path.append('../../moccasin/')
from matlab_parser import *
from converter import *



def main(argv):
    '''Usage: run-converter-tests.py [options]
Available options:
  -h   Print this help message
  -n   Don't drop into pdb upon a parsing exception -- keep going
  -p   Use parameters instead of species
  -x   Extra debugging -- print annotated Matlab parsing results
  -o   Create XPP (SBML is default)
'''

    try:
        options, unused = getopt.getopt(argv[1:], "npxo")
    except:
        raise SystemExit(main.__doc__)

    do_debug        = not any(['-n' in y for y in options])
    use_species     = not any(['-p' in y for y in options])
    do_print_interp = any(['-x' in y for y in options])
    output_sbml     = not any(['-o' in y for y in options])

    parser = MatlabGrammar()

    for f in glob.glob("converter-test-cases/valid_51*.m"):
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
            if output_sbml:
                print('----- SBML output ' + '-'*30)
            else:
                print('----- XPP output ' + '-'*30)
#            print('hello')
            sbml = converter.create_raterule_model(results, use_species,
                                                   output_sbml)
            print (sbml)
            # if output_sbml:
            #     out_path = f[0:len(f)-1]+'xml'
            #     file_out = open(out_path, 'w')
            #     file_out.write(sbml)
            #     file_out.close()
            # if output_xpp:
            #     print('----- xpp '+ '-'*30)
            #     xpp = converter.create_xpp_file(results, use_species)
            #     print(xpp)
            #     out_xpp_file = f[0:len(f)-2]+'from_moccasin.ode'
            #     file_xpp = open(out_xpp_file, 'w')
            #     file_xpp.write(xpp)
            #     file_xpp.close()
        except Exception as err:
            print('threw exception')
            if do_debug and not results:
                print('Object "results" contains the output of parse_string()')
                pdb.set_trace()


if __name__ == '__main__':
    main(sys.argv)
