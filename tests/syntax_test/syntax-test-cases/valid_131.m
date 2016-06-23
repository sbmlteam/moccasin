try
    x = 2
    while x > b
        warning('bar')
        [z] = 2*2
    end
catch
    try
        x = 1
    catch foo
        warning('bar')
        [z] = 2*2
    end
end
