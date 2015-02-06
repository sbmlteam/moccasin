% quick functions
f = @(x) 3*x.^2 + 2*x + 7;
t = (0:0.001:1);
plot(t,f(t),t,f(2*t),t,f(3*t));

% closures (linfunc below is a function that returns a function,
% and the outer functions arguments are held for the lifetime
% of the returned function.
linfunc = @(m,b) @(x) m*x+b;
C2F = linfunc(9/5, 32);
F2C = linfunc(5/9, -32*5/9);
