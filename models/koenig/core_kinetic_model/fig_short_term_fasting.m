%% FIG_SHORT_TERM_FASTING - Plot short term fasting curves.
% The glucose dependency data has to be calculated first.
%
% TODO: check the time conversions and scaling of the results
%
%   Matthias Koenig (matthias.koenig@charite.de)
%   Copyright 2014 Matthias Koenig
%   date:   2014-04-01
clear all, close all, format compact;

%% DATA PREPARATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
results_folder = '../../results/glucose_dependency';
res_file = strcat(results_folder, '/', 'glucose_dependency_350.mat');
fig_fname = strcat(results_folder, '/', 'short_term_fasting.tif')

conversion_factor = 12.5*60;   % (see ODE) [mmol/s] -> [µmol/min/kgbw]

% Load the simulation data [c_full, v_full, glc_ext, tspan]
% Matrix dimensions correspond to  v_full = zeros(Nt, Nv, Nsim);
load(res_file);

% Convert the time units if necessary
switch (name)
    case 'core'
        tspan = tspan
    case 'core_sbml'
        tspan = tspan/60; % [s] -> [min]
end

% glucose
glc_min = 3.6;
glc_max = 4.2;
tmp = find(glc_ext>=glc_min); glc_min_ind = tmp(1);
tmp = find(glc_ext<=glc_max); glc_max_ind = tmp(end);
clear tmp
y = glc_ext(glc_min_ind:glc_max_ind)

% time
t_max = 3900;   % [min] (65h) 
tmp = find(tspan>=t_max); t_max_ind = tmp(1);
clear tmp
t_offset=1;
xtime = tspan(t_offset:t_max_ind)/60;   % [h] ([min]->[h])

% Get the respective fluxes from the flux matrix 
%  -GLUT2 = -v1 => HGP
%  -GPI   = -v4 => GNG
%  +G16PI =  v5 = >GLY
v_kgbw_full = v_full * conversion_factor;  % [µmol/kg/min]
z_hgp = -v_kgbw_full(t_offset:t_max_ind, 1, glc_min_ind:glc_max_ind); 
z_gng = -v_kgbw_full(t_offset:t_max_ind, 4, glc_min_ind:glc_max_ind);
z_gly =  v_kgbw_full(t_offset:t_max_ind, 5, glc_min_ind:glc_max_ind);
z_hgp = squeeze(z_hgp)';
z_gng = squeeze(z_gng)';
z_gly = squeeze(z_gly)';

% calculate the relative contribution
z_frac = z_gng./z_hgp;

%% FIGURES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fig1 = figure('Name', 'Figure 3 - short term fasting', 'Color', [1 1 1]);

% Shift the time to account for overnight fasting state at beginning
% of simulation;
overnight_time = 9               % [h]
xtime = xtime +overnight_time;   % [h]

% HGP %
subplot(2,2,1)
psim = plot(xtime, z_hgp(2:end-1,:), 'k--'); hold on
psim = plot(xtime, z_hgp(1,:), '--', 'Color', [0.9 0.2 0], 'LineWidth', 2.0); hold on
psim = plot(xtime, z_hgp(end, :), '--', 'Color', [0 0.5 0], 'LineWidth', 2.0); hold off

ylabel('HGP [\mumol/kg/min]', 'FontWeight', 'bold')
axis square
xlim([overnight_time+0.5 70])
ylim([0 18])
set(gca,'XTick',10:10:70, 'FontWeight', 'bold')

% GNG %
subplot(2,2,2)
psim = plot(xtime, z_gng(2:end-1,:), 'k--'); hold on
psim = plot(xtime, z_gng(1,:), '--', 'Color', [0.9 0.2 0],'LineWidth', 2.0); hold on
psim = plot(xtime, z_gng(end, :), '--', 'Color', [0 0.5 0], 'LineWidth', 2.0); hold off
ylabel('GNG [\mumol/kg/min]', 'FontWeight', 'bold')
axis square
xlim([overnight_time+0.5 70])
ylim([0 12])
set(gca,'XTick',10:10:70, 'FontWeight', 'bold')

% GLY %
subplot(2,2,3)
psim = plot(xtime, z_gly(2:end-1,:), 'k--'); hold on
psim = plot(xtime, z_gly(1,:), '--', 'Color', [0.9 0.2 0],'LineWidth', 2.0); hold on
psim = plot(xtime, z_gly(end, :), '--', 'Color', [0 0.5 0], 'LineWidth', 2.0); hold off

xlabel('time [h]', 'FontWeight', 'bold')
ylabel('GLY [\mumol/kg/min]', 'FontWeight', 'bold')
axis square
xlim([overnight_time+0.5 70])
ylim([0 12])
set(gca,'XTick',10:10:70, 'FontWeight', 'bold')

% GNG/HGP %
subplot(2,2,4)
psim = plot(xtime, z_frac(2:end-1,:)*100, 'k--'); hold on
psim = plot(xtime, z_frac(1,:)*100, '--', 'Color', [0.9 0.2 0],'LineWidth', 2.0); hold on
psim = plot(xtime, z_frac(end,:)*100, '--', 'Color', [0 0.5 0], 'LineWidth', 2.0); hold off
xlabel('time [h]', 'FontWeight', 'bold')
ylabel('GNG/HGP [%]', 'FontWeight', 'bold')
axis square
xlim([overnight_time+0.5 70])
ylim([20 100])
set(gca,'XTick',10:10:70, 'FontWeight', 'bold')

% save the figure
saveas(fig1, fig_fname,'tif'); 
