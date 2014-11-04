Git scripts for MOCCASIN
========================

This directory contains scripts for use with our git repository on GitHub.  Please read the following and install any scripts or other items mentioned below as being part of our MOCCASIN project conventions.

pre-commit.sh
-------------

This is a pre-commit hook for git that runs Python source files through [pep8](https://pypi.python.org/pypi/pep8), a style guide checker.  The hook is invoked when you do a commit; if any issues are reported, it will abort the commit.  To force a commit anyway, you can override the hook by running `git commit --no-verify` instead of a plain `git commit`, but you should try to correct the issues instead.

The hook is per-user, not global, so you need to install manually it in your copy of the MOCCASIN repository.  To do that, follow these steps:

1. copy the file `pre-commit.sh` to the directory `.git/hooks/` at the top level of your MOCCASIN git repository
2. at the top-level of your repository, execute `git init`

