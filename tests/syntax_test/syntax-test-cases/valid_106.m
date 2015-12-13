% From MATLAB docs.
a = struct('b', 0, 'c', 'test'); % Create structure
a(2).b = 1;                      % Turn it into an array by creating another element
a(2).c = 'testing'
