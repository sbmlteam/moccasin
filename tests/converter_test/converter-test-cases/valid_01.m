function valid_01
tspan = [0 10];
initCond = [2]
[t, y] = ode45(@rigid, tspan, initCond)

function dy = rigid(t, y)
dy = [1]
end

end
