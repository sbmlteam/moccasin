function valid_03
tspan = [0 10];
initCond = [2]
[t, y] = ode45(@rigid, tspan, initCond)

function dy = rigid(t, y)
a = 0.5
b = 2*t
dy = [b]
end

end
