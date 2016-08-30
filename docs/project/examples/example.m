% Various parameter settings.  The specifics here are unimportant; this
% is just an example of a real input file.
%
tspan  = [0 300];
xinit  = [0; 0];
a      = 0.01 * 60;
b      = 0.0058 * 60;
c      = 0.006 * 60;
d      = 0.000192 * 60;

% A call to a MATLAB ODE solver
%
[t, x] = ode45(@f, tspan, xinit);

% A function that defines the ODEs of the model.
%
function dx = f(t, x)
  dx = [a - b * x(1); c * x(1) - d * x(2)];
end
