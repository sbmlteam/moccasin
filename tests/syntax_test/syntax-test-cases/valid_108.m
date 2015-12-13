% From MATLAB docs at
% https://en.wikibooks.org/wiki/MATLAB_Programming/Arrays/Struct_Arrays

a = struct('b', 0, 'c', 'test'); % Create structure
a(2).b = 1;                      % Turn it into an array by creating another element
a(2).c = 'testing'

% Dynamic field access:
str = 'c';
a(1).(str)
[a.('c')]

