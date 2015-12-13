% From MATLAB docs at
% https://en.wikibooks.org/wiki/MATLAB_Programming/Arrays/Struct_Arrays

foo = struct('field_a',{1,2,3,4},'field_b',{4,8,12,16})
value = 1;
[foo.field_b] = deal(value)
foo([foo.field_a] == 2)
