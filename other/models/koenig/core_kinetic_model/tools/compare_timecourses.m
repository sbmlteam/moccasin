function [] = compare_timecourses(sim_fname, ref_fname, scale)
% Control class to check that different model implementations
% give the same timecourse and flux results.
% Compare the integration results provided in the two files.
% Fluxes in [µmol/min/kgbw] are compared. 

format shortg

% load simulation 
load(sim_fname);
s = res;
clear res;

% load reference
load(ref_fname);
x = res;
clear res;

fprintf('\n* Difference c *\n');
fprintf('----------------\n');
fprintf('c(0)  c(end)\n');
fprintf('----------------\n');
delta_c = [(s.c(1,:) - x.c(1,:))' (s.c(end,:) - x.c(end,:))']

fprintf('\n* Difference v *\n');
fprintf('----------------\n');
fprintf('v(0)  v(end)\n');
fprintf('----------------\n');
if isfield(s, 'v_kgbw')
   sv = s.v_kgbw; 
else
   sv = s.v; 
end
if isfield(x, 'v_kgbw')
   xv = x.v_kgbw; 
else
   xv = x.v; 
end
delta_v = [(sv(1,:) - xv(1,:)*scale)' (sv(end,:) - xv(end,:)*scale)']

disp('******************************');
disp('* Delta c > 1E-6 *');
find(abs(delta_c) > 1E-6)
disp('* Delta v > 1E-6 *');
find(abs(delta_v) > 1E-6)

% disp('******************************');
% disp('* Delta c > 1E-8 *');
% find(abs(delta_c) > 1E-8)
% disp('* Delta v > 1E-8 *');
% find(abs(delta_v) > 1E-8)
% disp('******************************');
% disp('* Delta c > 1E-10 *');
% find(abs(delta_c) > 1E-10)
% disp('* Delta v > 1E-10 *');
% find(abs(delta_v) > 1E-10)
% disp('******************************');

end
