function xdot = case00004(time, x_values)
% function case00004 takes
%
% either	1) no arguments
%       	    and returns a vector of the initial values
%
% or    	2) time - the elapsed time since the beginning of the reactions
%       	   x_values    - vector of the current values of the variables
%       	    and returns a vector of the rate of change of value of each of the variables
%
% case00004 can be used with MATLABs odeN functions as 
%
%	[t,x] = ode23(@case00004, [0, t_end], case00004)
%
%			where  t_end is the end time of the simulation
%
%The variables in this model are related to the output vectors with the following indices
%	Index	Variable name
%	  1  	  S1
%	  2  	  S2
%
%--------------------------------------------------------
% output vector

xdot = zeros(2, 1);

%--------------------------------------------------------
% compartment values

compartment = 1;

%--------------------------------------------------------
% parameter values

k1 = 0.35;
k2 = 180;

%--------------------------------------------------------
% initial values of variables - these may be overridden by assignment rules
% NOTE: any use of initialAssignments has been considered in calculating the initial values

if (nargin == 0)

	% initial time
	time = 0;

	% initial values
	S1 = 0.15/compartment;
	S2 = 0/compartment;

else
	% floating variable values
	S1 = x_values(1);
	S2 = x_values(2);

end;

%--------------------------------------------------------
% assignment rules

%--------------------------------------------------------
% algebraic rules

%--------------------------------------------------------
% calculate concentration values

if (nargin == 0)

	% initial values
	xdot(1) = 0.15/compartment;
	xdot(2) = 0/compartment;

else

	% rate equations
	xdot(1) = ( - (compartment*k1*S1) + (compartment*k2*power(S2,2)))/compartment;
	xdot(2) = ( + 2 * (compartment*k1*S1) - 2 * (compartment*k2*power(S2,2)))/compartment;

end;
