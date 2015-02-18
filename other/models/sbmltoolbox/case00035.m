function xdot = case00035(time, x_values)
% function case00035 takes
%
% either	1) no arguments
%       	    and returns a vector of the initial values
%
% or    	2) time - the elapsed time since the beginning of the reactions
%       	   x_values    - vector of the current values of the variables
%       	    and returns a vector of the rate of change of value of each of the variables
%
% case00035 can be used with MATLABs odeN functions as 
%
%	[t,x] = ode23(@case00035, [0, t_end], case00035)
%
%			where  t_end is the end time of the simulation
%
%The variables in this model are related to the output vectors with the following indices
%	Index	Variable name
%	  1  	  S1
%	  2  	  S2
%	  3  	  S3
%	  4  	  S4
%
%--------------------------------------------------------
% output vector

xdot = zeros(4, 1);

%--------------------------------------------------------
% compartment values

compartment = 1;

%--------------------------------------------------------
% parameter values

k1 = 750;
k2 = 250;

%--------------------------------------------------------
% initial values of variables - these may be overridden by assignment rules
% NOTE: any use of initialAssignments has been considered in calculating the initial values

if (nargin == 0)

	% initial time
	time = 0;

	% initial values
	S1 = 0.001/compartment;
	S2 = 0.001/compartment;
	S3 = 0.002/compartment;
	S4 = 0.001/compartment;

else
	% floating variable values
	S1 = x_values(1);
	S2 = x_values(2);
	S3 = x_values(3);
	S4 = x_values(4);

end;

%--------------------------------------------------------
% assignment rules

%--------------------------------------------------------
% algebraic rules

%--------------------------------------------------------
% calculate concentration values

if (nargin == 0)

	% initial values
	xdot(1) = 0.001/compartment;
	xdot(2) = 0.001/compartment;
	xdot(3) = 0.002/compartment;
	xdot(4) = 0.001/compartment;

else

	% rate equations
	xdot(1) = ( - (compartment*multiply(k1,multiply(S1,S2))) + (compartment*k2*S3*S4))/compartment;
	xdot(2) = ( - (compartment*multiply(k1,multiply(S1,S2))) + (compartment*k2*S3*S4))/compartment;
	xdot(3) = ( + (compartment*multiply(k1,multiply(S1,S2))) - (compartment*k2*S3*S4))/compartment;
	xdot(4) = ( + (compartment*multiply(k1,multiply(S1,S2))) - (compartment*k2*S3*S4))/compartment;

end;


%---------------------------------------------------
%Function definitions

%function multiply

function returnValue = multiply(x, y)

returnValue = x*y;


