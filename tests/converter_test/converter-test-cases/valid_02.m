function valid_02
tspan = [0 10];
initCond = [2]
[t, y] = ode45(@rigid, tspan, initCond)

function dy = rigid(t, y)
a = 0.5
dy = [a]
end

end
