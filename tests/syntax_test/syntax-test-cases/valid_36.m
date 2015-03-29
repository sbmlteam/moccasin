fhandle = @humps;
sqr = @(x) x.^2;
S.a = @sin;  S.b = @cos;  S.c = @tan;
structfun(@(x)x(linspace(1,4,3)), S, 'UniformOutput', false)
