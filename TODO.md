TODO
========
This is a list that delineates what is left to be done when it comes to achieving a file structure that matches the standards for open sourced Python projects.

1. Update all README files after the file directory move
2. Evolve current tests into UNIT tests or acceptance tests
3. Check that documentation includes - quickstart and index files, etc.
4. Check whether we want Python eggs (Mike's initial file structure having individual test folders in parser and converter suggests this, but I went with having a single package.

In setup.py
5. Check whether the required_install needs to be expanded.
6. Check how to integrate testing into package building (tox, or test_required)
7. Check that author_email is correct
8. test_suite must point to the right place (may need to be a folder test inside package moccasin)
9. Packaging for a particular OS?

On the github doc folder
10. Quickstart" documentation (how to quickly install and use your project)
11. A list of non-Python dependencies (if any) and how to install them
12. Look into doctesting as an alternative to UnitTests

For providing a script that users that user (python script [command][input]) create a folder scripts, place them there and set setup.py scripts= ['script name']

