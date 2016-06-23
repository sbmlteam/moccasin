function [x] = valid_78(a)
    x = a(2)
end

function [x] = other(y)
    x = y
end

function [x] = another()
    valid_78(@other)
end
