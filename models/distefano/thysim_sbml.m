% this version is from thysimconst.m and will be used in getplot.cgi
% modified to allow tspan and ICs to be passed in as parameters
% Thyroid hormone equations implementation based on 
% May 10, 2012 equations.

% Clear previous variables, if any
clc; clear all;

% Process argument list
arg_list = argv();
IC1  = str2num(arg_list{1});
IC2  = str2num(arg_list{2});
IC3  = str2num(arg_list{3});
IC4  = str2num(arg_list{4});
IC5  = str2num(arg_list{5});
IC6  = str2num(arg_list{6});
IC7  = str2num(arg_list{7});
IC8  = str2num(arg_list{8});
IC9  = str2num(arg_list{9});
IC10 = str2num(arg_list{10});
IC11 = str2num(arg_list{11});
IC12 = str2num(arg_list{12});
IC13 = str2num(arg_list{13});
IC14 = str2num(arg_list{14});
IC15 = str2num(arg_list{15});
IC16 = str2num(arg_list{16});
IC17 = str2num(arg_list{17});
IC18 = str2num(arg_list{18});
IC19 = str2num(arg_list{19});
t1   = str2num(arg_list{20});
t2   = str2num(arg_list{21});
dial1= str2num(arg_list{22});
dial2= str2num(arg_list{23});
dial3= str2num(arg_list{24});
dial4= str2num(arg_list{25});
inf1 = str2num(arg_list{26});
inf4 = str2num(arg_list{27});

% Declare global variables for use in ODE function
global p1 p2 p3 p4 p5 p6 p7 p8 p9 p10 p11 p12 p13 p14 p15 p16 p17 p18 p19;
global p20 p21 p22 p23 p24 p25 p26 p27 p28 p29 p30 p31 p32 p33 p34 p35 p36;
global p37 p38 p39 p40 p41 p42 p43 p44 p45 p46 p47 p48 kdelay u1 u4;
global d1 d2 d3 d4;

% Declare parameters
u1 = inf1;                     % Infusion into plasma T4
u4 = inf4;                     % Infusion into plasma T3
kdelay = 5/8;                  % (n-1)/k = t; n comps, t = 8hr
d1=dial1;
d2=dial2;
d3=dial3;
d4=dial4;

p1  =  0.00174155;          %S4
p2  =  8;                   %tau
p3  =  0.868;               %k12
p4  =  0.108;               %k13
p5  =  584;                 %k31free
p6  =  1503;                %k21free
p7  =  0.000289;            %A
p8  =  0.000214;            %B
p9  =  0.000128;            %C
p10 = -8.83*10^-6;          %D
p11 =  0.88;                %k4absorb; originally 0.881
p12 =  0.0189;              %k02
p13 =  0.00998996;          %VmaxD1fast
p14 =  2.85;                %KmD1fast
p15 =  6.63*10^-4;          %VmaxD1slow
p16 =  95;                  %KmD1slow
p17 =  0.00074619;          %VmaxD2slow
p18 =  0.075;               %KmD2slow
p19 =  3.3572*10^-4;        %S3
p20 =  5.37;                %k45
p21 =  0.0689;              %k46
p22 =  127;                 %k64free
p23 =  2043;                %k54free
p24 =  0.00395;             %a
p25 =  0.00185;             %b
p26 =  0.00061;             %c
p27 = -0.000505;            %d
p28 =  0.88;                %k3absorb
p29 =  0.207;               %k05
p30 =  1166;                %Bzero
p31 =  581;                 %Azero
p32 =  2.37;                %Amax
p33 = -3.71;                %phi
p34 =  0.53;                %kdegTSH-HYPO
p35 =  0.037;               %VmaxTSH
p36 =  23;                  %K50TSH
p37 =  0.118;               %k3
p38 =  0.29;                %T4P-EU
p39 =  0.006;               %T3P-EU
p40 =  0.037;               %KdegT3B
p41 =  0.0034;              %KLAG-HYPO
p42 =  5;                   %KLAG
p43 =  1.3;                 %k4dissolve
p44 =  0.12*d2;             %k4excrete; originally 0.119
p45 =  1.78;                %k3dissolve
p46 =  0.12*d4;             %k3excrete; originally 0.118
% p47 and p48 are only used in converting mols to units.
p47 =  3;                   %Vp
p48 =  3.5;                 %VTSH

% Equations are in a separate function
function [dqdt] = ODEss(t,q)
global p1 p2 p3 p4 p5 p6 p7 p8 p9 p10 p11 p12 p13 p14 p15 p16 p17 p18 p19;
global p20 p21 p22 p23 p24 p25 p26 p27 p28 p29 p30 p31 p32 p33 p34 p35 p36;
global p37 p38 p39 p40 p41 p42 p43 p44 p45 p46 p47 p48 kdelay u1 u4;
global d1 d2 d3 d4;

% Auxillary equations
q4F = (p24+p25*q(1)+p26*q(1)^2+p27*q(1)^3)*q(4);         %FT3p
q1F = (p7 +p8 *q(1)+p9 *q(1)^2+p10*q(1)^3)*q(1);         %FT4p
SR3 = (p19*q(19))*d3; % Brain delay
SR4 = (p1 *q(19))*d1; % Brain delay
fCIRC = 1+(p32/(p31*exp(-q(9)))-1)*(1/(1+exp(10*q(9)-55)));
SRTSH = (p30+p31*fCIRC*sin(pi/12*t-p33))*exp(-q(9));
fdegTSH = p34+p35/(p36+q(7));
fLAG = p41+2*q(8)^11/(p42^11+q(8)^11);
f4 = p37+5*p37/(1+exp(2*q(8)-7));

% ODEs
q1dot = SR4+p3*q(2)+p4*q(3)-(p5+p6)*q1F+p11*q(11)+u1;           %T4dot
q2dot = p6*q1F-(p3+p12+p13/(p14+q(2)))*q(2);                    %T4fast
q3dot = p5*q1F-(p4+p15/(p16+q(3))+p17/(p18+q(3)))*q(3);         %T4slow
q4dot = SR3+p20*q(5)+p21*q(6)-(p22+p23)*q4F+p28*q(13)+u4;       %T3pdot
q5dot = p23*q4F+p13*q(2)/(p14+q(2))-(p20+p29)*q(5);             %T3fast
q6dot = p22*q4F+p15*q(3)/(p16+q(3))+p17*q(3)/(p18+q(3))-p21*q(6);%T3slow
q7dot = SRTSH-fdegTSH*q(7);                                     %TSHp
q8dot = f4/p38*q(1)+p37/p39*q(4)-p40*q(8);                      %T3B
q9dot = fLAG*(q(8)-q(9));                                       %T3B LAG
q10dot= -p43*q(10);                                             %T4PILLdot
q11dot=  p43*q(10)-(p44+p11)*q(11);                             %T4GUTdot
q12dot= -p45*q(12);                                             %T3PILLdot
q13dot=  p45*q(12)-(p46+p28)*q(13);                             %T3GUTdot

% Delay ODEs
q14dot= -kdelay*q(14) +q(7);                                    %delay1
q15dot= kdelay*(q(14) -q(15));                                  %delay2
q16dot= kdelay*(q(15) -q(16));                                  %delay3
q17dot= kdelay*(q(16) -q(17));                                  %delay4
q18dot= kdelay*(q(17) -q(18));                                  %delay5
q19dot= kdelay*(q(18) -q(19));                                  %delay6

% ODE vector
dqdt(1)=q1dot;
dqdt(2)=q2dot;
dqdt(3)=q3dot;
dqdt(4)=q4dot;
dqdt(5)=q5dot;
dqdt(6)=q6dot;
dqdt(7)=q7dot;
dqdt(8)=q8dot;
dqdt(9)=q9dot;
dqdt(10)=q10dot;
dqdt(11)=q11dot;
dqdt(12)=q12dot;
dqdt(13)=q13dot;
dqdt(14)=q14dot;
dqdt(15)=q15dot;
dqdt(16)=q16dot;
dqdt(17)=q17dot;
dqdt(18)=q18dot;
dqdt(19)=q19dot;
dqdt=dqdt';

endfunction

% Declare solve conditions and solve
q0 = [IC1; IC2; IC3; IC4; IC5; IC6; IC7; IC8; IC9; IC10; IC11; IC12; IC13; IC14; IC15; IC16; IC17; IC18; IC19];
tspan = [t1 t2];

vopt = odeset ('NormControl','on', 'InitialStep',1);
[t,x]=ode45(@ODEss, tspan, q0, vopt);

% Printing the output for the interface
[n m] = size(x);

% T4
printf("START_q1_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,1));
end
printf("END_q1_END\n");

% T3
printf("START_q4_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,4));
end
printf("END_q4_END\n");

% TSH
printf("START_q7_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,7));
end
printf("END_q7_END\n");

% time
printf("START_t_START\n");
for i = 1:n
  printf("%0.6f\n",t(i));
end
printf("END_t_END\n");

% q2
printf("START_q2_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,2));
end
printf("END_q2_END\n");

% q3
printf("START_q3_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,3));
end
printf("END_q3_END\n");

% q5
printf("START_q5_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,5));
end
printf("END_q5_END\n");

% q6
printf("START_q6_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,6));
end
printf("END_q6_END\n");

% q8
printf("START_q8_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,8));
end
printf("END_q8_END\n");

% q9
printf("START_q9_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,9));
end
printf("END_q9_END\n");

% q10
printf("START_q10_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,10));
end
printf("END_q10_END\n");

% q11
printf("START_q11_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,11));
end
printf("END_q11_END\n");

% q12
printf("START_q12_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,12));
end
printf("END_q12_END\n");

% q13
printf("START_q13_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,13));
end
printf("END_q13_END\n");

% q14
printf("START_q14_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,14));
end
printf("END_q14_END\n");

% q15
printf("START_q15_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,15));
end
printf("END_q15_END\n");

% q16
printf("START_q16_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,16));
end
printf("END_q16_END\n");

% q17
printf("START_q17_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,17));
end
printf("END_q17_END\n");

% q18
printf("START_q18_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,18));
end
printf("END_q18_END\n");

% q19
printf("START_q19_START\n");
for i = 1:n
  printf("%0.6f\n",x(i,19));
end
printf("END_q19_END\n");

%%% script end %%%
