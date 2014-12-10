%% sim_glucose_glycogen_dependency - Generate steady state flux data
% under constant glc_ext and glycogen.
% Necessary for Figure 5.
%
%   Matthias Koenig (matthias.koenig@charite.de)
%   Copyright 2014 Matthias Koenig
%   date:   2014-04-01

results_folder = '../../results/glucose_glycogen_dependency';
res_file = strcat(results_folder, '/', 'glucose_glycogen_dependency.mat');
% name = 'core'
name = 'core_sbml'

% Varying glucose and glycogen concentrations
glc_ext     = 2:0.5:20;                                      % [mM]
tmp = logspace(0, 1, 8)-1;
glycogen =  [tmp linspace(10, 490, 10)  500-tmp(end:-1:1)];  % [mM]
clear tmp

% glc_ext     = 2:2:20;                                      % [mM]
% tmp = logspace(0, 1, 5)-1;
% glycogen =  [tmp linspace(10, 490, 5)  500-tmp(end:-1:1)];  % [mM]
% clear tmp

% Timepoints
tspan = (0:100:200);  % [min]
switch (name)
    case 'core'
        % core model time in [min]
        dydt_fun = @(t,y) dydt_model_glucose(t,y);
    case 'core_sbml'
        % sbml model time in [s]
        dydt_fun = @(t,y) dydt_model_glucose_sbml(t,y);
        tspan = 60 * tspan;
end

% Constant glycogen for simulation
global glycogen_constant;
glycogen_constant = 1;

% Get the size of the vectors
x0 = initial_concentrations();
[ctmp, vtmp, ~] = dydt_fun(0, x0);  
Nglc = numel(glc_ext);
Ngly = numel(glycogen);
Nsim = Nglc*Ngly;
Nt = numel(tspan);
Nc = numel(ctmp); 
Nv = numel(vtmp);
clear vtmp ctmp

% Matrices of fluxes and concentrations
c_full = zeros(Nglc, Ngly, Nt, Nc);
v_full = zeros(Nglc, Ngly, Nt, Nv);

% Simulate for all glucose and glycogen concentrations
count = 1; 
count_max = numel(glc_ext)*numel(glycogen);
tic;
for kglc=1:numel(glc_ext)
    for kgly=1:numel(glycogen)

        % information about the loops
        if (mod(count, 20) == 1)
            fprintf('%3.2f %%  \t [%6.2f\t->\t%6.2f ] min\n', count/count_max*100, toc/60,  toc/60/count*(count_max-count) );
        end
        count = count + 1; 
        
        x0(32) = glc_ext(kglc);   % [mM]
        x0(17) = glycogen(kgly);  % [mM]
        
        % integrate
        [t,c] = ode15s(dydt_fun, tspan , x0, odeset('RelTol', 1e-9, 'AbsTol', 1e-9));

        % Calculate fluxes from the ODE system
        v  = zeros(Nt, Nv);
        for kt=1:Nt
            [~, v(kt, :), ~] = dydt_fun(t(kt), c(kt, :));
        end
        clear kt
        
        % Save concentrations and fluxes
        c_full(kglc, kgly, :, :) = c;
        v_full(kglc, kgly, :, :) = v;
    end
end
save(res_file, 'glc_ext', 'glycogen', 'tspan', 'c_full', 'v_full', '-v7.3')

