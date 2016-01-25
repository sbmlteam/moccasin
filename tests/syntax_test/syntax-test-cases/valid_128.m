for t = 1:1:26
    if 0<t<=4
        x1d(t) = 0.5*t;
        x2d(t) = 0.5*t;
    elseif 4 < t && t <= 7.
        x1d(t) = 0.5*t;
        x2d(t) = 3.33;
    elseif 7<t<=10
        x1d(t) = 0.5*t;
        x2d(t) = 10/3 - 0.5*(t-40/3);
    elseif 10<t<=26
        x1d(t) = 0.5*t;
        x2d(t) = 0;
    end
end
