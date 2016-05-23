function valid_05

tspan = [0 10]
initCond = [0 0]
[t, y] = ode45(@foo, tspan, initCond)

function [dydt] = foo(t, y)
dydt(1) = 11
dydt(2) = 22
dydt = dydt'
end

end
