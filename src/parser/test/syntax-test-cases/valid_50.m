function valid_50
% parameter values
% time is in minutes
tspan=[0 300]; 
xzero=[0;0];
% parameter values  (Time is in minutes)
a=0.01*60;
b=0.0058*60;
c=0.006*60;
d=0.000192*60;
[t,y]=ode45(@g,tspan,xzero);
figure
plot(t,y(:,2))

function y=g(t,x)
% ODE for  mRNA and protein production and decay (Thattai-Van Oudenaarden)
y=[a-b*x(1); c*x(1)-d*x(2)];
end

end
