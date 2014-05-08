% function [t, c, v] = sim_single()
%SIM_SINGLE Simulation with hepatic glucose model.
%   Returns:
%       t:      vector of time points
%       c:      matrix of concentrations for the time points t
%       v:      matrix of fluxes for the time points t
%
%   What are the units ?
%   time [min]
%   
%
%   Matthias Koenig (matthias.koenig@charite.de)
%   Copyright 2014 Matthias Koenig
%   date:   2014-03-27
%
% TODO: scaling to represent single hepatocytes and whole liver results
% correctly with the respective simulation volumes and glycogen storage 
% density
clear all, close all, format compact
results_folder = '../../results';

% Initial concentrations
x0 = initial_concentrations();

%global glycogen_constant;
%glycogen_constant = 1;

% Model to integrate: core is the classic implentation used for the
% publication whereas the sbml version gives the same results but is
% rewritten to represent the model properly in SBML.
tspan = 0:1:2000;
% name = 'core'
name = 'core_sbml'
switch (name)
    case 'core'
        % core model time in [min]
        dydt_fun = @(t,y) dydt_model_glucose(t,y);
    case 'core_sbml'
        % sbml model time in [s]
        dydt_fun = @(t,y) dydt_model_glucose_sbml(t,y);
        tspan = 60 * tspan;
end
func2str(dydt_fun)

% Integration (relative and absolute tolerances controlled to be 
% sure about the numerical values.
[t,c] = ode15s(dydt_fun, tspan , x0, odeset('RelTol', 1e-9, 'AbsTol', 1e-9));

% Calculate fluxes from the ODE system
[~, vtmp, ~] = dydt_fun(0, x0);   % get the flux names
Nv = numel(vtmp);
Nt = numel(t);
v  = zeros(Nt, Nv);      % [mmol/s]
v_kgbw = zeros(Nt, Nv);  % [µmol/kg/min]
for k=1:Nt
    [~, v(k, :), ~, v_kgbw(k,:)] = dydt_fun(t(k), c(k, :));
end

% Save data for comparison
res.v = v;          
res.v_kgbw = v_kgbw;
res.c = c;
res.t = t;
sim_fname = strcat(results_folder, '/', name, '.mat')
save(sim_fname, 'res');


%% Compare the results to reference implementation
% In case of the sbml_core the scaling due to min -> seconds as time units
% has to be provided for the comparison function.
ref_fname = strcat(results_folder, '/', 'standard.mat')
switch (name)
    case 'core'
        compare_timecourses(sim_fname, ref_fname, 1.0) 
    case 'core_sbml'
        compare_timecourses(sim_fname, ref_fname, 1)
end

%% Create figure
fig_single(t, c, v);