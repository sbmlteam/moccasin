%% create_figures_from_paper - Reproduce the simulation results of the 
% Plos Computational Biology Paper.
%
%   Matthias Koenig (matthias.koenig@charite.de)
%   Copyright 2014 Matthias Koenig
%   date:   2014-04-01

% Figure 2 - Create the hormone dose response curves
sim_hormone_response();

% Create data for figure 3 and 4
sim_glucose_dependency();

% Figure 3 - HGP, GNG and GLY contributions
fig_short_term_fasting;

% Figure 4 - Glycogen metabolism
fig_glycogen_metabolism;

% Figure 5 - Glucose and glycogen response
sim_glucose_glycogen_dependency();
fig_glycogen_metabolism;

