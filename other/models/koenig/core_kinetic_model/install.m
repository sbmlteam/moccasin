%% Initializes the matlab scripts
% Adds the necessary subfolders to the path.

%   Matthias Koenig (2014-03-27)
%   Copyright Matthias Koenig 2014 All Rights Reserved.
clc
fprintf('---------------------------------\n');
fprintf('# Install Hepatic Glucose Model #\n');
fprintf('---------------------------------\n');
fprintf('Add path\n');
folder = pwd;
pinfo = {'', 'tools'};
for kp = 1:numel(pinfo)
    p = strcat(folder, '/', pinfo{kp}); 
    addpath(p);
    fprintf('\t%s\n', p);
end
fprintf('... added to path.\n');
savepath();
fprintf('---------------------------------\n');
