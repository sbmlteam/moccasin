function valid_101(A, xlsfile, x1, x2)
persistent dblArray;

if isempty(dblArray) 
    xlswrite(xlsfile, A);
end

dblArray = xlsread(xlsfile, 'Sheet1', [x1 ':' x2])
fprintf('\n');
