function valid_50

tspan = [0 300]; 
xinit = [0; 0];

a = 0.01 * 60;
b = 0.0058 * 60;
c = 0.006 * 60;
d = 0.000192 * 60;

% Matlab's ode45 is designed to handle the following general problem:
% given a set of differential equations, dX/dt = f(t, X), 
% with initial values X(t_0) = xinit, it solves for values of the
% vector of variables X at different times t.  The function defining
% the differential equations is given as "f".

[t, x] = ode45(@f, tspan, xinit);

figure
plot(t, y(:, 2))

function dx = f(t, x)
  dx = [a - b * x(1); c * x(1) - d * x(2)];
end

end
