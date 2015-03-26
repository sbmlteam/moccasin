function[Y]=parse_fails
tspan=[0 12];
initCond = [1,1,1]
[T,Y] = ode45(@rigid,tspan,initCond)

%% ODE system function
function dy = rigid(t,y)
k1=1;
dy=[k1*y(1); cos(k1); cos(k1*y(1))];
end

end
