function[Tsim SimData]=valid_52
%model_example_Hill kinetics
close all

k = [4.2416    5.9816    0.1009    1.1549    1.3618    1.4219    0.0051    0.0972    0.0012   56.8583    0.0111    0.0014]; % parameters
tspan = [0 1.5]; % integration times
x0 = [1 1 1]; % initial conditions
I = 1; % input signal, could also be defined as just another parameter in k

[Tsim, SimData] = ode15s(@rhss, tspan, x0, [], k, I);

%% plotting
figure
subplot(3,1,1);
plot(Tsim, SimData(:,1))
subplot(3,1,2);
plot(Tsim, SimData(:,2))
subplot(3,1,3);
plot(Tsim, SimData(:,3))

function dxdt = rhss(t,x, k, I)
% three component incoherent feed-forward network
dxdt = [k(1)*I*x(1)/(x(1)+k(7)) - k(2)*x(1)/(x(1)+k(8));k(3)*x(1)*x(2)/(x(2)+k(9)) - k(4)*x(2)/(x(2)+k(10));k(5)*x(1)*x(3)/(x(3)+k(11)) - k(6)*x(2)*x(3)/(x(3)+k(12))]
end

end

