Testing in Moccasin
=======================
Moccasin defines acceptance test suites for each of its modules (matlab_parsing and converter). We have chosen _py.test_ as the Python automated testing ecosystem because it provides support for setuptools, support for "normal" assert statements, and has less boilerplate.

### File structure
The files _converter_test/test_converterModule_ and _syntax_test/test_syntaxModule_ dynamically generate a parametrized call to a test function for each combination of test matlab file and matching result file. In this way, we avoid needing an acceptance test function per matlab file, but instead have a single test function per test module.

### Running tests
To run Moccasin's acceptance tests:

* Type ```python setup.py test``` from the top folder to run tests for both modules or simply,
 
* Type ```py.test``` from each test directory to run tests pertaining to that module. 

Test coverage reports
---------------------------

In order to determine what proportion of Moccasin code is actually being tested by the defined acceptance tests, Moccasin reports code coverage statistics using the Python coverage package. The metric used here is statement coverage, which reports whether each executable statement was encountered. 

To display coverage reports type from the main directory:

* ```coverage run setup.py test ```. This will gather coverage data for the whole project.

Then, you can use either:

* ```coverage report ```, which will print the report or,

* ```coverage html```, which will create a new folder (htmlcov) folder containing a detailed navigable report (index.html) of uncovered code statements per python file.

Testing in different Python environments
---------------------------
Acceptance tests can be run in either Python 2.7 or Python 3.3. To ensure compliance, Moccasin uses **Tox**. Tox is a very simple idea implemented extremely well. When we type the command ```tox``` from the top directory, a source distribution of Moccasin is created and installed on different isolated virtual environments for testing. 

Tox automatically prints a coverage report on the command line and generates the htmlcov folder for the whole project.

Contributing to Moccasin
---------------------------
In order to ensure a smooth multi-developer effort and monitor testing results, code coverage and build correctness throughout development, Moccasin uses **TravisCI** for continuous integration of changes into the code base.