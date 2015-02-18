% SIM_HORMONE_RESPONSE
% Simulates data for Figure 2: insulin, glucagon and epinephrine dose-response curves
% with the experimental data and the resulting gamma curves.
% author: Matthias Koenig

close all; clear all; clc;

% which model to integrate for comparison
name = 'core_sbml'
%name = 'core'
switch (name)
    case 'core'
        dydt_fun = @(t,y) dydt_model_glucose(t,y);
    case 'core_sbml'
        dydt_fun = @(t,y) dydt_model_glucose_sbml(t,y);
end
func2str(dydt_fun)


glc_min  = 2;
glc_max  = 20;
glc_step = 0.01;
glc_ext = glc_min:glc_step:glc_max;

results_folder = '../../results/hormone_response';

% Not necessary to integrate, instantaneous
% hormonal response. Change the external glucose concentration
% and get the respective hormone and gamma values back from the
% integration routine
x0 = initial_concentrations();
glc_ext_index = 32;

% hormones and gamma depending on glc_ext
ins = zeros(size(glc_ext));
epi = zeros(size(glc_ext));
glu = zeros(size(glc_ext));
ins_data = zeros(size(glc_ext));
epi_data = zeros(size(glc_ext));
glu_data = zeros(size(glc_ext));
gamma = zeros(size(glc_ext));

for k = 1:numel(glc_ext)
   x0(glc_ext_index) = glc_ext(k);
   [~, ~, hormones] = dydt_fun(0, x0);
   ins(k) = hormones.ins;
   epi(k) = hormones.epi;
   glu(k) = hormones.glu;
   ins_norm(k) = hormones.ins_norm;
   epi_norm(k) = hormones.epi_norm;
   glu_norm(k) = hormones.glu_norm;
   gamma(k) = hormones.gamma;
end

data_fname = strcat(results_folder, '/Hormone_Response.mat')
save(data_fname, 'glc_ext', 'ins', 'epi', 'glu')

%% make the plot
h_axis = {  [glc_min glc_max 0 800] 
            [glc_min glc_max 0 200] 
            [glc_min 8 0 7000]
			[glc_min glc_max 0 1]};
x_name = 'glucose [mM]';

fig_fname = strcat(results_folder, '/Hormone_Response.tif')
fig1 = figure('Name', 'Hormone response', 'Color', [1 1 1], 'Position', [0 0 900 900]);

    % Insulin
	sph_i=subplot(2,2,3);
    hp1=plot(glc_ext, ins,'-k');
    lx1=xlabel(x_name);
    lx2=ylabel('insulin [pmol/l]');
    axis(h_axis{1});
    axis square
    grid on
    set(sph_i, 'XTick',[2 5 8 11 14 17 20]);
    set(sph_i, 'yTick',[200 400 600 800]);
    set(hp1,'LineWidth',2.0);
	
    % Glucagon
	sph_g=subplot(2,2,1);
    hp1g = plot(glc_ext, glu,'-k');
    lx1g = xlabel(x_name);
    lx2g = ylabel('glucagon [pmol/l]');
    axis(h_axis{2});
    axis square
    grid on
    set(sph_g, 'XTick',[2 5 8 11 14 17 20])
    set(sph_g, 'yTick',[50 100 150 200])
    set(hp1g,'LineWidth',2.0);
	
    % Epinephrine
	sph_e=subplot(2,2,2);
    hp1e=plot(glc_ext, epi,'-k');
    lx1e=xlabel(x_name);
    lx2e=ylabel('epinephrine [pmol/l]');
    axis(h_axis{3});
    axis square
    grid on
    set(sph_e, 'XTick',[2 3 4 5 6 7 8])
    set(sph_e, 'yTick',[1500 3000 4500 6000])
    set(hp1e,'LineWidth',2.0);
			
	sph_gamma1 = subplot(2,2,4);
	hp1c=plot(glc_ext, gamma, '-k');
	xlabel(x_name)
    ylabel('gamma')
    axis square
    axis([glc_min glc_max 0 1])
    grid on
    set(hp1c,'LineWidth',2.0);
    set(sph_gamma1, 'XTick',[2 5 8 11 14 17 20])
    set(sph_gamma1, 'yTick',[0.2 0.4 0.6 0.8 1])
        
saveas(fig1, fig_fname,'tif'); 
