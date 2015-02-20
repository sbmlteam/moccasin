function xdot = case00029(time, x_values)
% function case00029 takes
%
% either	1) no arguments
%       	    and returns a vector of the initial values
%
% or    	2) time - the elapsed time since the beginning of the reactions
%       	   x_values    - vector of the current values of the variables
%       	    and returns a vector of the rate of change of value of each of the variables
%
% case00029 can be used with MATLABs odeN functions as 
%
%	[t,x] = ode23(@case00029, [0, t_end], case00029)
%
%			where  t_end is the end time of the simulation
%
%The variables in this model are related to the output vectors with the following indices
%	Index	Variable name
%	  1  	  S1
%
%--------------------------------------------------------
% output vector

xdot = zeros(1, 1);

%--------------------------------------------------------
% compartment values

compartment = 1;

%--------------------------------------------------------
% parameter values


%--------------------------------------------------------
% initial values of variables - these may be overridden by assignment rules
% NOTE: any use of initialAssignments has been considered in calculating the initial values

if (nargin == 0)

	% initial time
	time = 0;

	% initial values
	S1 = 7/compartment;

else
	% floating variable values
	S1 = x_values(1);

end;

%--------------------------------------------------------
% assignment rules
S1 = 7;

%--------------------------------------------------------
% algebraic rules

%--------------------------------------------------------
% calculate concentration values

if (nargin == 0)

	% initial values
	xdot(1) = S1;

else

	% rate equations
	xdot(1) = 0;

end;
