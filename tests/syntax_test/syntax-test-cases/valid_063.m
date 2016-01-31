!echo 'foo'

% Matlab shell commands have an annoying feature: they don't respect
% elipsis continuation or comments on the same line.  The next two
% lines should therefore result in 2 separate statements: one a 
% shell command with "echo ..." as the argument, and the second
% as simply the string 'foo'.

% FIXME: parsing this properly is currently (2016-01-31) broken because of
% the need to handle continuations correctly in other contexts.  Fixing
% this will not be terribly hard but not worth the time right now.

% !echo ...
% 'foo'
