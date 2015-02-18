function [names] = names_v()
% NAMES_V Returns metabolite names of the model.
%
% Returns:
%   names:  cell array of names of the reactions

names = {
'GLUT2'     % v1   
'Glucokinase'      % v2   
'G6Pase'           % v3   
'GPI'              % v4
'G16PI'            % v5
'UPGase'           % v6
'PPase'           % v7 
'GS'              % v8 
'GP'              % v9
'NTK (GTP)'       % v10            
'NTK (UTP)'       % v11
'AK'              % v12
'PFK2'            % v13
'FBP2'            % v14
'PFK1'            % v15
'FBP1'            % v16
'ALD'             % v17
'TPI'             % v18
'GAPDH'           % v19
'PGK'             % v20
'PGM'             % v21
'EN'              % v22
'PK'              % v23
'PEPCK'      % v24
'PEPCK_{mito}'      % v25
'PC'              % v26
'LDH'             % v27
'LacT'            % v28
'PyrT'            % v29
'PepT'            % v30
'PDH'             % v31
'CS'              % v32
'NDK_{mito}'        % v33
'oaa_{flx}'         % v34
'acoa_{flx}'        % v35
'vcit_{flx}'        % v36
};
