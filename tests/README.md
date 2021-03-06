Testing in MOCCASIN
=======================

MOCCASIN defines acceptance test suites for each of its modules (`matlab_parsing` and `converter`). We have chosen **py.test** as the Python automated testing ecosystem because it provides support for setuptools, support for "normal" assert statements, and has less boilerplate.

### File structure

The files `converter_test/test_converterModule.py` and `syntax_test/test_syntaxModule.py` dynamically generate a parametrized call to a test function for each combination of test matlab file and matching result file. In this way, we avoid needing an acceptance test function per matlab file, but instead have a single test function per test module.

### Running tests

To run MOCCASIN's acceptance tests:

* Type `python setup.py test` from the top folder to run tests for both modules or simply,
 
* Type `py.test` from each test directory to run tests pertaining to that module. 

Test coverage reports
---------------------------

In order to determine what proportion of MOCCASIN code is actually being tested by the defined acceptance tests, MOCCASIN reports code coverage statistics using the Python coverage package. The metric used here is statement coverage, which reports whether each executable statement was encountered. 

To display coverage reports type from the main directory:

* `coverage run setup.py test`. This will gather coverage data for the whole project.

Then, you can use either:

* `coverage report`, which will print the report or,

* `coverage html`, which will create a new folder (`htmlcov`) folder containing a detailed navigable report (`index.html`) of uncovered code statements per Python file.

Testing in different Python environments
---------------------------

Acceptance tests can be run in either Python 2.7 or Python 3.3. To ensure compliance, MOCCASIN uses **Tox**. Tox is a very simple idea implemented extremely well. When we type the command `tox` from the top directory, a source distribution of MOCCASIN is created and installed on different isolated virtual environments for testing. 

Tox automatically prints a coverage report on the command line and generates the `htmlcov` folder for the whole project.

Contributing to MOCCASIN
---------------------------

In order to ensure a smooth multi-developer effort and monitor testing results, code coverage and build correctness throughout development, MOCCASIN uses **TravisCI** for continuous integration of changes into the code base.


### Random Tips

* We had trouble with tests taking very long on the [Travis CI](https://travis-ci.com) service connected to GitHub.  Running the whole suite of tests (3 test sets for *converter_test*, *evaluate_test* and *syntax_test*) that the overall builds failed because they exceeded the time limit imposed by Travis CI.  We discovered a way to split up the Travis CI builds such that [different parts of the tests were run in parallel](https://docs.travis-ci.com/user/speeding-up-the-build/).  This didn't solve the problem of how slowly the tests ran on Travis CI, but it made it so that the individual processes did not exceed the maximum timeout.

