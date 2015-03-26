function sauro1


%STAT0=0.1;
x0={0,0,0,0};
%x0(14)=STAT0;
ts=0; te=10;

 myopt=odeset('reltol',1e-9,'abstol',1e-10); 

% parameters (1st line from the paper. 2nd line for this model)
% IFNb mRNA
r0=3e-3; tao1=2.5;
r1=r0; k1=log(2)/tao1;
% IFNb protein (environment)
C=5e5; vmax2=20 *3600; NA=6.02e23;
r2= 1e9*C*vmax2/NA; KK2=2e-3;
% STAT2Pn
TJtot=1e-4;k5=3600; tao3=0.56;
r3=TJtot*k5; k3=log(2)/tao3; KK3=4.3e-3;
% IRF7 mRNA
k11=3600e-7; tao6=1;
r4=k11; k4=log(2)/tao6;

[t,ys]=ode15s(@resi,linspace(ts,te,300),x0,myopt);

subplot(2,2,1), plot(t,ys(1:300,1))
xlabel('time (h)')
 ylabel('concentration (uM)')
title('IFNb mRNA')
subplot(2,2,2), plot(t,ys(1:300,2))
xlabel('time (h)')
ylabel('concentration (uM)')
title('IFNb protein')
subplot(2,2,3), plot(t,ys(1:300,3))
xlabel('time (h)')
ylabel('concentration (uM)')
title('STAT2Pn ')
subplot(2,2,4), plot(t,ys(1:300,4))
xlabel('time (h)')
ylabel('concentration (uM)')
title('IRF7 mRNA')


function y=resi(t,x)

% viral antagonism parameters, 1st (myf) for IFNb induction, 2nd (myfs)
%  for CPFS binding
y=zeros(4,1);
b1=0.4;
b4=0.2;
myf=exp(-b1*t);
myfs=exp(-b4*t);

% x(1)  [IFNb_mRNA]
y(1)=  r1*myf- k1*x(1);
% x(2)  [IFNb_env]
y(2)=   r2*x(1)/(KK2+x(1));
% x(3)  [STATP2n]
y(3)=    r3*x(2)/(KK3+x(2))- k3*x(3);
% x(4)  [IRF7m]
y(4)=    r4*x(3)*myfs- k4*x(4);

end

end
