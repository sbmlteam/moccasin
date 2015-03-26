function[Y]=valid_58
tspan=[0 12];
initCond = [1]
[T,Y] = ode45(@rigid,tspan,initCond)


%% ODE system function
function dy = rigid(t,y)
b1=0.4;
myf=exp(-b1*t);
dy=[myf*y(1)];
end

end
