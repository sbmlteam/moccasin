%% fig_glycogen_metabolism - Plot glycogen time courses.
% The glucose dependency data has to be calculated first.
%
%   Matthias Koenig (matthias.koenig@charite.de)
%   Copyright 2014 Matthias Koenig
%   date:   2014-04-01

close all, clear all

%% DATA PREPARATION %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
results_folder = '../../results/glucose_dependency';
res_file_200 = strcat(results_folder, '/', 'glucose_dependency_200.mat');
res_file_500 = strcat(results_folder, '/', 'glucose_dependency_500.mat');
fig_fname = strcat(results_folder, '/', 'glycogen_metabolism.tif')

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Experimental data for glycogenolysis
% Rothman 1991
rothman1991 = [
3.9758	369.097	3.88951	373.845	4.04596	483.752	NaN	NaN	NaN	NaN	3.88969	372.489	4.5773	354.855
6.81345	287.032	6.55356	308.739	NaN	NaN	7.05665	388.798	7.40293	361.664	6.81015	311.455	6.98301	299.923
9.89522	299.948	9.72079	323.013	9.61854	445.807	9.89604	293.842	10.4874	354.905	9.72299	306.731	10.0712	265.35
13.1554	259.948	12.8064	307.435	12.8796	399.702	13.0723	241.63	NaN	NaN	12.7287	248.411	NaN	NaN
15.9038	205.019	15.7378	165.669	15.7974	358.343	15.6468	205.017	16.4027	315.607	15.7281	237.582	14.534	200.258
21.7464	70.0617	21.8198	160.971	21.7184	276.982	22.0807	131.801	22.0694	215.248	22.0786	147.405	NaN	NaN
28.0852	66.7233	27.6523	101.319	27.3765	240.395	28.0791	111.499	28.2365	214.622	27.6523	101.319	27.303	150.163
39.9951	36.2951	39.9069	55.2903	39.8212	55.2895	40.1592	89.2138	40.1567	108.21	39.9925	55.291	39.7355	55.9672
45.6464	49.9115	45.7296	67.5513	45.6465	49.2331	45.7305	60.7671	46.5819	98.7662	45.4751	49.2317	45.7306	60.0886
51.469	62.851	51.7255	66.2453	51.4658	86.5959	52.0709	45.8955	51.8109	68.2813	51.5544	64.887	51.5596	26.2167
63.9771	42.6043	63.5493	39.2085	63.2936	29.7084	64.4928	29.7185	64.1416	92.8093	63.6352	37.174	63.8092	17.5011
];

magnusson1992 = [
4	282.446	60.566
13.5	163.062	43.094
17	113.561	33.194
19.5	124.626	26.206
22.5	96.6722	22.7118
];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Experimental data for glycogen synthesis
radziuk2001 = [
    1.59234	200.986	1.59347	200.659	1.59461	200.331
29.6751	232.499	119.513	248.682	59.5685	201.718
59.4327	241.062	148.735	258.229	90.3629	218.152
89.1893	249.954	178.453	278.268	119.031	234.255
119.492	254.584	238.493	297.691	149.327	240.852
149.229	269.377	NaN	NaN	179.046	260.564
179.503	282.204	NaN	NaN	208.773	277.98
209.244	295.685	NaN	NaN	238.52	289.822
238.976	311.79	NaN	NaN	NaN	NaN
];

taylor1996 = [
    0	206.604	21.132
120	247.358	17.359
150	259.434	18.113
180	279.057	19.622
260	295.66	21.887
];

%% GLYCOGENOLYSIS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load the simulation data [c_full, v_full, glc_ext, tspan]
% Matrix dimensions correspond to  v_full = zeros(Nt, Nv, Nsim);
% Initial full glycogen;
load(res_file_500);

% Convert the time units if necessary
switch (name)
    case 'core'
        tspan = tspan     % [min]
    case 'core_sbml'
        tspan = tspan/60; % [s] -> [min]
end

% plot boundaries
glc_min = 3.5; % [mM]
glc_max = 5;   % [mM]
t_max = 3900;  % [min]

% indeces of plot boundaries 
tmp = find(glc_ext>=glc_min); glc_min_ind = tmp(1);
tmp = find(glc_ext<=glc_max); glc_max_ind = tmp(end);
tmp = find(tspan>=t_max); t_max_ind = tmp(1);
clear tmp;

x1 = glc_ext(glc_min_ind:glc_max_ind);
y1 = tspan(1:t_max_ind)/60;      % [min] -> [h]
z1 = c_full(1:t_max_ind, 17, glc_min_ind:glc_max_ind);  % glycogen [mM]
z1 = squeeze(z1)';
clear glc_min_ind glc_max_ind t_max_ind glc_min glc_max t_max t_offset tspan
x1
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% [2] glycogen synthesis
load(res_file_200);

% Convert the time units if necessary
switch (name)
    case 'core'
        tspan = tspan     % [min]
    case 'core_sbml'
        tspan = tspan/60; % [s] -> [min]
end

% plot boundaries
glc_min = 5.5;  % [mM]
glc_max = 8;    % [mM]
t_max = 300;    % [min]

% indeces of plot boundaries
tmp = find(glc_ext>=glc_min); glc_min_ind = tmp(1);
tmp = find(glc_ext<=glc_max); glc_max_ind = tmp(end);
tmp = find(tspan>=t_max); t_max_ind = tmp(1);
clear tmp

x2 = glc_ext(glc_min_ind:glc_max_ind);
y2 = tspan(1:t_max_ind); % [min]
z2 = c_full(1:t_max_ind, 17, glc_min_ind:glc_max_ind); % glycogen [mM]
z2 = squeeze(z2)'; 
x2


%% FIGURE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fig1 = figure('Name', 'Glycogen Metabolism', 'Color', [1 1 1]);

colororder = [
         0         0    1.0000
         0    0.5000         0
    1.0000         0         0
         0    0.7500    0.7500
    0.7500         0    0.7500
    0.7500    0.7500         0
    0.2500    0.2500    0.2500
    0    0.2500    0.2500
    ];

% Glycogenolysis %
subplot(1,2,1)
psim = plot(y1, z1(2:end,:), 'k--'); hold on
psim = plot(y1, z1(1,:), '--', 'Color', [0.9 0.2 0],'LineWidth', 2.0); hold on
psim = plot(y1, z1(end,:), '--', 'Color', [0 0.5 0], 'LineWidth', 2.0); hold on
for k=1:7
    xtmp = rothman1991(:,2*(k-1)+1);
    ytmp = rothman1991(:,2*(k-1)+2);
    pdata = plot(xtmp(~isnan(xtmp)), ytmp(~isnan(ytmp)), '-s', ...
        'MarkerSize',4.0, 'MarkerEdgeColor', [0.2 0.2 0.2]);
    set(pdata, 'Color', colororder(k,:) );
    set(pdata, 'MarkerFaceColor', colororder(k,:) );
    %set(pdata, 'MarkerFaceColor', [0 0 0]);
end

hp1 = plot(magnusson1992(:,1), magnusson1992(:,2), '-s', 'MarkerSize',4.0, 'MarkerEdgeColor', [0.2 0.2 0.2]);
he1 =errorbar(magnusson1992(:,1), magnusson1992(:,2), magnusson1992(:,3),'.k');
set(hp1,'Color',colororder(8,:) );
set(hp1, 'MarkerFaceColor', colororder(8,:) );
set(he1,'MarkerSize',2.0);
hold off

xlabel('time [h]', 'FontWeight', 'bold')
ylabel('glycogen [mM]', 'FontWeight', 'bold')
axis square
axis([0 65 0 500])
set(gca, 'FontWeight', 'bold')


% Glycogen synthesis %
subplot(1,2,2)
p2 = plot(y2, z2(2:end, :), 'k--'); hold on
p2 = plot(y2, z2(1,:), '--', 'Color', [0.9 0.2 0],'LineWidth', 2.0); hold on
p2 = plot(y2, z2(end,:), '--', 'Color', [0 0.5 0], 'LineWidth', 2.0); hold on
p2 = plot(y2, z2(4,:), 'b--', 'LineWidth', 2.0); hold on

%title('Glycogen synthesis [5-10mM glucose]', 'FontWeight', 'bold')
for k=1:3
    xtmp = radziuk2001(:,2*(k-1)+1);
    ytmp = radziuk2001(:,2*(k-1)+2);
    p1 = plot(xtmp(~isnan(xtmp)), ytmp(~isnan(ytmp)), '-s', ...
                'MarkerSize',4.0, 'MarkerEdgeColor', [0.2 0.2 0.2]);
    set(p1, 'Color', colororder(k,:) );
    set(p1, 'MarkerFaceColor', colororder(k,:) );                
end
hp1 = plot(taylor1996(:,1), taylor1996(:,2), '-s', 'MarkerSize',6.0, 'MarkerEdgeColor', [0.2 0.2 0.2]);
he1 = errorbar(taylor1996(:,1), taylor1996(:,2), taylor1996(:,3),'.k');
set(hp1,'Color',colororder(4,:) );
set(hp1, 'MarkerFaceColor', colororder(4,:) );
set(hp1, 'Marker', 'p')
set(he1,'MarkerSize',4.0);
set(he1,'Color', [0 0 0]);

xlabel('time [min]', 'FontWeight', 'bold')
ylabel('glycogen [mM]', 'FontWeight', 'bold')
axis square
axis([-10 300 180 340])
set(gca, 'FontWeight', 'bold')

saveas(fig1, fig_fname,'tif'); 