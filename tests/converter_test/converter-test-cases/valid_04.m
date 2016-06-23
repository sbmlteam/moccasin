function valid_04

tspan = [0 10]
initCond = [2]
[t, y] = ode45(@foo, tspan, initCond)
output = [t, y];

function dy = foo(t, y)
a = 0.5
dy = [a]
end

end
