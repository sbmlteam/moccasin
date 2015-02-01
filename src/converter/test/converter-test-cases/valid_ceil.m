function[Y]=valid_ceil
tspan=[0 12];
initCond = [1 2 3] 
[T,Y] = ode45(@rigid,tspan,initCond)
figure
subplot(2,2,1);
plot(T,Y(:,1),'r-');
title('dy_1 concentration over time');
subplot(2,2,2);
plot(T,Y(:,2),'b-.');
title('dy_2 concentration over time');
subplot(2,2,3);
plot(T,Y(:,3),'g:');
title('dy_3 concentration over time');
subplot(2,2,3);
xlabel('Simulation Time');
ylabel('Species Concentration');
subplot(2,2,4);
plot(T,Y(:,1),'r-',T,Y(:,2),'b-.',T,Y(:,3),'g:')
title('Species concentrations over time');

%% ODE system function
function dy = rigid(t,y)
k1=1;
k2=5;
k3=6;
dy=[ceil(y(2)*y(3)*k1); -y(1)*y(3)*k2;y(1)*y(2)*k3];
end

end
