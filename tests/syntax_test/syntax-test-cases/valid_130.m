function s = procStruct(s)
    if numel(s) > 1
        for i=1:numel(s)
            s(i) = procStruct(s(i));
        end
    else
        s.data = abs(s.data);
    end
end
