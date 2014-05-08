%function [t, c_full, v_full, glc_ext] = sim_glucose_dependency()
%% SIM_GLUCOSE_DEPENDENCY Set varying external glucose concentrations and
% simulate the time courses.
%
%   Matthias Koenig (matthias.koenig@charite.de)
%   Copyright 2014 Matthias Koenig
%   date:   2014-04-01
clear all, close all, format compact;
results_folder = '../../results/glucose_dependency';

% Variation in external glucose concentration
glycogen = [200 350 500];  % [mM]
glc_ext = 2.0:0.2:12;      % [mM]

% Model to integrate: core is the classic implentation used for the
% publication whereas the sbml version gives the same results but is
% rewritten to represent the model properly in SBML.
tspan = (0:0.02:70)*60;   % [min] 70h
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

% Get the dimensions of the system
x0 = initial_concentrations();
[ctmp, vtmp, ~] = dydt_fun(0, x0);   % get the flux names
Nsim = numel(glc_ext);
Nt = numel(tspan);
Nc = numel(ctmp); 
Nv = numel(vtmp);
clear vtmp ctmp

c_full = zeros(Nt, Nc, Nsim);
v_full = zeros(Nt, Nv, Nsim);

% Simulate for all glucose concentrations

for kgly = 1:numel(glycogen)
    glyglc = glycogen(kgly);
    fprintf('*** GLYCOGEN = %s ***\n', num2str(glyglc));
    res_file = strcat(results_folder, '/', 'glucose_dependency_',num2str(glyglc),'.mat');
    for ks=1:Nsim
        fprintf('%3.2f \n', ks/Nsim*100); % progress

        % set external glucose & glycogen
        % indices can be looked up in names_c
        x0(32) = glc_ext(ks); % [mM]
        x0(17) = glyglc;    % [mM]

        % integrate
        [t,c] = ode15s(dydt_fun, tspan , x0, odeset('RelTol', 1e-9, 'AbsTol', 1e-9));

        % Calculate fluxes from the ODE system
        v  = zeros(Nt, Nv);      
        for kt=1:Nt
            [~, v(kt, :), ~] = dydt_fun(t(kt), c(kt, :));
        end
        clear kt

        % Save concentrations and fluxes
        c_full(:, :, ks) = c;
        v_full(:, :, ks) = v;
    end
    clear ks
    save(res_file, 'c_full', 'v_full', 'glc_ext', 'tspan', 'name', '-v7.3')
end
