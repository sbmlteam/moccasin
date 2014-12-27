Project conventions for MOCCASIN code
=====================================

This is an evolving set of guidelines for working on the project.

GitHub repository workflow model
--------------------------------

* We use the approach of keeping two main branches in the GitHub central repository:
    - `master`: the main branch; here, the source code at `HEAD` should always reflect a usage, production-ready state. 
    - `develop`: where development takes place; developers should create their branches from the `develop` branch, and should push their changes back to it.  (Other projects might call this an _integration_ branch.)
* Feature branches live in the repositories of developers and are generally short-lived (existing only for the length of the development of a given feature).  They are branched off of `develop` and merged back into `develop` when completed, after which developers can delete them from their private repositories.
* Merges from feature development branches to `develop` are performed with the `--no-ff` flag (i.e., `git merge --no-ff featurebranchname`), so that the merge always creates a new commit and preserves the history of the individual commits on the feature development branch.  Here's a summary of the basic process:
```csh
> git checkout -b myfeature develop
# Do some work. Commit a lot to the branch "myfeature".
# Eventually:
> git checkout develop
> git merge --no-ff myfeature
> git push origin develop
> git branch -d myfeature
```
* At suitable times (basically, when releases are prepared), the merge czar (currently Mike Hucka) merges changes from the `develop` branch to the `master` branch.


Coding guidelines
-----------------

* Indent code blocks with 4 spaces.
* Use spaces, not tabs, for code indentation.
* Try to keep lines _under_ 80 characters long.  Of course, sometimes code readability is improved if a complex statement is _not_ broken across lines, but in general, shorter lines help code readability.  The 80 character guideline is used by many projects and organizations (e.g., it's [what Google uses too](https://google-styleguide.googlecode.com/svn/trunk/pyguide.html)), but it's a general guideline for this project, not a rule cast in stone.
* Try to follow [pep8](http://pep8.readthedocs.org) guidelines *except* for the following:
    - E221: multiple spaces before operators.  This rule unfortunately causes aligned assignment statements to be flagged by `pep8`; that is, it flags the case where you align the equals `=` signs for several assignments across multiple lines.  The alignment is desirable because sometimes it helps code readability.
    - E226: missing whitespace around operators.  If this rule is left in, then `pep8` flags constructs such as `print(stuff + "-"*70)` because of the lack of spaces around the `*`.  However, adding spaces in such cases arguably makes the result _less_ easily understood.
    - E241: multiple spaces after a comma.  This again is a case where it flags situations in which you may want to align code across multiple lines for readability reasons.
    - E303: too many blank lines.  If you have more than one blank line anywhere in your file, this will cause `pep8` to flag it.  This is frankly ridiculous.  File readability is often enhanced by having more than one line between parts of a file.
    - E501: line too long.  Sometimes it makes sense to let a line be longer than 80 characters.
* If there's a line of code that knowingly breaks the `pep8` conventions, you can write the comment `# noqa` at the end of the line to make `pep8` shut up about it.  (Note: turns out this doesn't always work; `pep8` will sometimes flag something even if you write the comment on the line.  This appears to be a bug in `pep8`.  If that happens, and you really don't want to rewrite the code, then go ahead and leave it.)
* Use the git `prepare-commit-msg` hook discussed below.
* Follow the [Google Python coding style](https://google-styleguide.googlecode.com/svn/trunk/pyguide.html) when it comes to other issues.


Git and GitHub guidelines
-------------------------

* Hard-wrap commit messages and use the convention that the first line of the message is a short summary at most 50 characters long, with the remaining lines generally kept to less than 80 characters.  This is a variation of the _50/72 formatting_ guideline discussed in [this StackOverflow question](http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting), except that it doesn't require the 72 part.


Git configuration
-----------------

* To make code formatting be more consistent across different authors, use the `prepare-commit-msg` hook found in [dev/git-scripts](../dev/git-scripts).  Instructions for how to install it can be found in the README file in that [git-scripts](../dev/git-scripts)  directory.  The hook runs code through [pep8](http://pep8.readthedocs.org), a code style checker, and reports any issues at the time the user starts a `git commit`.
