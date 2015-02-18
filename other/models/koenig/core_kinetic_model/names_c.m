function [names] = names_c()
% NAMES_C Returns metabolite names of the model.
%
% Returns:
%   names:  cell array of names of metabolite names

names = {
'atp'       % S1 : atp
'adp'       % S2 : adp
'amp'       % S3 : amp
'utp'       % S4 : utp
'udp'       % S5 : udp
'gtp'       % S6 : gtp
'gdp'       % S7 : gdp
'nad'       % S8 : nad
'nadh'      % S9 : nadh
'p'         % S10 : p
'pp'        % S11 : pp
'h2o'       % S12 : h2o
'co2'       % S13 : co2
'h'         % S14 : h
'glc1p'     % S15 : glc1p
'udpglc'    % S16 : udpglc
'glyglc'    % S17 : glyglc

'glc'       % S18 : glc
'glc6p'     % S19 :  glc6p
'fru6p'     % S20 :  fru6p
'fru16bp'   % S21 :  fru16bp
'fru26bp'   % S22 :  fru26bp
'grap'      % S23 :  grap
'dhap'      % S24 :  dhap
'bpg13'     % S25 :  bpg13
'pg3'       % S26 :  pg3
'pg2'       % S27 :  pg2
'pep'       % S28 :  pep
'pyr'       % S29 :  pyr
'oaa'       % S30 :  oaa
'lac'       % S31 :  lac
 
'glc_{ext}'   % S32 :  glc_ext
'lac_{ext}'   % S33 :  lac_ext
 
'co2_{mito}'  % S34 :  co2_mito
'p_{mito}'    % S35 :  p_mito
'oaa_{mito}'  % S36 :  oaa_mito
'pep_{mito}'  % S37 :  pep_mito
'acoa_{mito}' % S38 :  acoa_mito
'pyr_{mito}'  % S39 :  pyr_mito
'cit_{mito}'  % S40 :  cit_mito
 
'atp_{mito}'  % S41 :  atp_mito
'adp_{mito}'  % S42 :  adp_mito
'gtp_{mito}'  % S43 :  gtp_mito
'gdp_{mito}'  % S44 :  gdp_mito

'coa_{mito}'  % S45 : coa_mito
'nadh_{mito}' % S46 : nadh_mito
'nad_{mito}'  % S47 : nad_mito
'h_{mito}'    % S48 : h_mito
'h2o_{mito}'  % S49 : h2o_mito
};