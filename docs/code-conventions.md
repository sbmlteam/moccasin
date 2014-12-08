Project conventions for MOCCASIN code
=====================================

This is an evolving set of guidelines for working on the project.

Coding guidelines
-----------------

* Try to keep lines _under_ 80 characters long.  Of course, sometimes code readability is improved if a complex statement is not broken across lines, but in general, shorter lines help code readability.  This is a general guideline, not a rule cast in stone.
* Use spaces, not tabs, for code indentation.
* Try to follow [pep8](http://pep8.readthedocs.org) guidelines *except* for the following:
    - E221: multiple spaces before operators.  This rule unfortunately causes aligned assignment statements to be flagged by `pep8`; that is, it flags the case where you align the equals `=` signs for several assignments across multiple lines.  The alignment is desirable because sometimes it helps code readability.
    - E226: missing whitespace around operators.  If this rule is left in, then `pep8` flags constructs such as `print(stuff + "-"*70)` because of the lack of spaces around the `*`.  However, adding spaces in such cases arguably makes the result _less_ easily understood.
    - E241: multiple spaces after a comma.  This again is a case where it flags situations in which you may want to align code across multiple lines for readability reasons.
    - E303: too many blank lines.  If you have more than one blank line anywhere in your file, this will cause `pep8` to flag it.  This is frankly ridiculous.  File readability is often enhanced by having more than one line between parts of a file.
    - E501: line too long.  Sometimes it makes sense to let a line be longer than 80 characters.
* If there's a line of code that knowingly breaks the `pep8` conventions, you can write the comment `# noqa` at the end of the line to make `pep8` shut up about it.


Git and GitHub guidelines
-------------------------

* Hard-wrap commit messages and use the 50/72 formatting guideline discussed in [this StackOverflow question](http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting)


Git configuration
-----------------

* To make code formatting be more consistent across different authors, use the `prepare-commit-msg` hook found in [dev/git-scripts](../dev/git-scripts).  Instructions for how to install it can be found in the README file in that [git-scripts](../dev/git-scripts)  directory.  The hook runs code through [pep8](http://pep8.readthedocs.org), a code style checker, and reports any issues at the time the user starts a `git commit`.
