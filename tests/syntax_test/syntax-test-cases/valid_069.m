a = {1, 2}
% The following should parse as a cell array reference:
a{1}
% The following should parse as a command called with one argument:
% Note: if you use 'a' here instead of another identifier, then
% Matlab will given an error that 'a' has previously been used
% as a variable.
b {1}
% The following should parse as an array of 3 elements:
[a {1} a]
