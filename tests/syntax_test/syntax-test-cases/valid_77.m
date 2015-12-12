function [x] = valid_77(a)
    x = str2func(a);
    y = x(2)
    z = other(2)
end

function [x] = other(y)
    x = y
end

function [x] = another()
    valid_77('other')
end

