function [] = fig_single(t, c, v)
%% SIM_SINGLE_ANALYSIS Generates images for simple simulation.
%   Graphical analysis of solution.
%   Called with the results of the integration procedure.
%       t:      time vector
%       c:      concentration matrix
%       v:      flux matrix
%       mpars:  parameters for simulation


%% Offset to not show initial large variations
offset = 0;  % offset in time units
offset_ind = find(t>=offset);
if numel(offset_ind) == 0
    offset = 1;
else
    offset = offset_ind(1);
end

timelabel = 'time [units]';

%% Create figures
s_name = names_c();
v_name = names_v();
close all

% All concentrations
fig1 = figure('Name','Concentrations', 'Color',[1 1 1]);
for k=1:length(s_name)
    y = c(:,k);
    subplot(5,10,k)  
    y_upper = 1.05*max(y);
    y_lower = -0.01;
    
    if numel(find(imag(y))) > 0
       warning('!!! Imaginary concentrations !!!') 
    end
    
    plot(t(offset:end), y(offset:end, :)), axis([t(1) t(end) y_lower y_upper]),
    title(strcat(s_name{k}, ' [mM]'), 'FontWeight', 'bold')
    %label('time [min]')
    %ylabel(strcat(s_name{k}, ' [mM]'), 'FontWeight', 'bold')
end

% All fluxes
fig2 = figure('Name','Fluxes', 'Color',[1 1 1]);
for k=1:( length(v_name)-3 )
    y = v(:,k);
    
    if numel(find(imag(y))) > 0
       warning('!!! Imaginary fluxes !!!') 
    end
    
    subplot(5,7,k)  
    plot(t(offset:end), y(offset:end, :)), 
    title(v_name{k}, 'FontWeight', 'bold')
    %xlabel('timelabel')
    %ylabel(v_name{k}, 'FontWeight', 'bold')
end

% Important concentrations
fig3 = figure('Name','Important Concentrations', 'Color',[1 1 1]);
s_interest = [4 5 15:29 31 37 39 43 44];
for p=1:length(s_interest)
    k = s_interest(p);
    y = c(:,k);
    subplot(5,5,p)  
    plot(t(offset:end), y(offset:end, :))
    %ylabel(strcat(s_name{k},' [mM]'), 'FontWeight', 'bold')
    title(s_name{k}, 'FontWeight', 'bold')
    %xlabel(timelabel)
end

% Switch analysis
fig4 = figure('Name','Futile Cycles', 'Color',[1 1 1]);
subplot(2,2,1)
y = [v(:, 2), v(:,3), (v(:,2)-v(:,3))];
plot(t(offset:end), y(offset:end, :))
title('Glucose switch')
legend('GK', 'G6Pase', 'GK-G6Pase')
xlabel(timelabel)
ylabel('v')
grid

subplot(2,2,2)
y = [v(:, 8) v(:,9), v(:,8)-v(:,9)];
plot(t(offset:end), y(offset:end, :))
title('Glycogen switch')
legend('GS', 'GP', 'GS-GP')
xlabel(timelabel)
ylabel('v')
grid

subplot(2,2,3)
y = [v(:, 15) v(:,16), v(:,15)-v(:,16)];
plot(t(offset:end), y(offset:end, :)), 
title('PFK switch'), 
legend('PFK1', 'FBP1', 'PFK1-FBP1')
xlabel(timelabel)
ylabel('v')
grid

subplot(2,2,4)
y = [v(:, 23) v(:,25), v(:,23)-v(:,25)];
plot(t(offset:end), y(offset:end, :)), 
title('PK - PEPCK switch'), 
legend('PK', 'PEPCK', 'PK-PEPCK')
xlabel(timelabel)
ylabel('v')
grid
