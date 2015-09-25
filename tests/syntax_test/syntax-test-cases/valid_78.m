function [x] = valid_78(a)
    x = a(2)
end

function [x] = other(y)
    x = y
end

valid_78(@other)
