Git scripts for MOCCASIN
========================

This directory contains scripts for use with our git repository on GitHub.  Please read the following and install any scripts or other items mentioned below as being part of our MOCCASIN project conventions.

python.prepare-commit-msg
-------------------------

This hook script runs pep8 on python files that are about to be committed.  If pep8 reports anything, the report is inserted as comments into the commit message template.  This approach was the best that I could come up with in order to handle the following situation: if you use an editor like Emacs, and your commit message is thrown into an editing buffer, you may not see messages printed on stdout or stderr by the git commit command.  By putting the pep8 output into the commit message template, it helps ensure you see it before committing.

Running pep8 is not something you want to do on a commit hook, because you may want to ignore pep8's warnings.  Using prepare-commit-msg, you can ignore the warnings by deleting the comments from the commit message.  (But of course, it's better to take the opportunity to go back and fix the issues before completing the commit.)

To use it, every member of the project needs to do the following:

1. copy the script to the `.git/hooks/` subdirectory of their local git repository
2. rename the script to `prepare-commit-msg`
3. make it executable (`chmod +x` on the file)
