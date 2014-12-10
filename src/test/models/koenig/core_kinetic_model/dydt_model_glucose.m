function [dydt, v, hormones] = dydt_model_glucose(t, y)
% MODEL_GLYCOLYSIS
%   author: Matthias Koenig 
%           Charite Berlin
%           Computational Systems Biochemistry Berlin
%           matthias.koenig@charite.de
%   date:   121203
%

%% Scaling hepatic glucose metablism
scale_gly = 12.5;
scale_glyglc = 12.5;

%% Concentrations
atp         = y(1);
adp         = y(2);
amp         = y(3);
utp         = y(4);
udp         = y(5);
gtp         = y(6);
gdp         = y(7);
nad         = y(8);
nadh        = y(9);
p           = y(10);
pp          = y(11);
co2         = y(13);
glc1p       = y(15);
udpglc      = y(16);
glyglc      = y(17);
glc         = y(18);
glc6p       = y(19);
fru6p       = y(20);
fru16bp     = y(21);
fru26bp     = y(22);
grap        = y(23);
dhap        = y(24);
bpg13       = y(25);
pg3         = y(26);
pg2         = y(27);
pep         = y(28);
pyr         = y(29);
oaa         = y(30);
lac         = y(31);
glc_ext     = y(32);
lac_ext     = y(33);
co2_mito    = y(34);
p_mito      = y(35);
oaa_mito    = y(36);
pep_mito    = y(37);
acoa_mito   = y(38);
pyr_mito    = y(39);
cit_mito    = y(40);
atp_mito    = y(41);
adp_mito    = y(42);
gtp_mito    = y(43);
gdp_mito    = y(44);
coa_mito    = y(45);
nadh_mito   = y(46);
nad_mito    = y(47);

%% Hormonal response & phosphorylation state
% insulin
x_ins1 = 818.9; % [pmol/l]
x_ins2 = 0;     % [pmol/l]
x_ins3 = 8.6;   % [mM]
x_ins4 = 4.2;   % [-]
ins = x_ins2 + (x_ins1-x_ins2) * glc_ext^x_ins4/(glc_ext^x_ins4 + x_ins3^x_ins4); % [pmol/l]
ins_norm = max(0.0, ins-x_ins2);

% glucagon
x_glu1 = 190;  % [pmol/l]
x_glu2 = 37.9; % [pmol/l]
x_glu3 = 3.01; % [mM]
x_glu4 = 6.40; % [-]
glu = x_glu2 + (x_glu1-x_glu2)*(1 - glc_ext^x_glu4/(glc_ext^x_glu4 + x_glu3^x_glu4)); % [pmol/l]
glu_norm = max(0.0, glu-x_glu2); 

% epinephrine
x_epi1 = 6090;  % [pmol/l]
x_epi2 = 100;   % [pmol/l]
x_epi3 = 3.10;  % [mM]
x_epi4 = 8.40;  % [-]
epi = x_epi2 + (x_epi1-x_epi2) * (1 - glc_ext^x_epi4/(glc_ext^x_epi4 + x_epi3^x_epi4)); % [pmol/l]
epi_norm = max(0.0, epi-x_epi2);

% gamma
K_val = 0.1;  % [-];
epi_f = 0.8; % [-];
K_ins = (x_ins1-x_ins2) * K_val; % [pmol/l];
K_glu = (x_glu1-x_glu2) * K_val; % [pmol/l];
K_epi = (x_epi1-x_epi2) * K_val; % [pmol/l];
gamma = 0.5 * (1 - ins_norm/(ins_norm+K_ins) + max(glu_norm/(glu_norm+K_glu), epi_f*epi_norm/(epi_norm+K_epi)) ); % [-]

% store the hormone response for analysis
hormones.ins = ins;
hormones.ins_norm = ins_norm;
hormones.glu = glu;
hormones.glu_norm = glu_norm;
hormones.epi = epi;
hormones.epi_norm = epi_norm;
hormones.gamma = gamma;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%   Glucose import/export             %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% *********************************** %
% v1 : GLUT2 - Transporter
% *********************************** %
% T0011_cytoYext
% GLUT 2
% 1 C00031_ext -> 1 C00031_cyto
% glucose_ext -> glucose
% facilitated diffusion, low affinity, high-turnover transport system
% Lebergue2009, Elliot1982, Gold1991, Ciaraldi1986, Thorens1996,
% Nelson2008
% reversibel Michaelis Menten Kinetics; symmetrical transport of glucose by
% GLUT2
%
%v1_deltag = 0;                              % [kJ/mol]
%v1_keq = keq(v1_deltag);                    % []
%v1_td = (glc_ext - glc/v1_keq);

v1_keq = 1;
v1_km = 42;  % [mM]
v1_Vmax = 420;
v1 = (scale_gly*v1_Vmax)/v1_km * (glc_ext - glc/v1_keq)/(1 + glc_ext/v1_km + glc/v1_km);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%   Glucokinase / G6Pase              %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% *********************************** %
% v2 : Glucokinase
% *********************************** %
% R00299_2.7.1.2_cyto
% ATP:D-glucose 6-phosphotransferase
% C00002 + C00031 <=> C00008 + C00092	
% glucose + atp -> glucose_6P + adp 
% Delta G0' = -16.7 kJ/mol 
% Morito1994, Agius2008
% GK has sigmoidal kinetics in glucose with high km for glucose with n
% about 1.5 - 1.8.
% Hyperobolic in the ATP response. 
% In addition the activity is regulated by GKRP. The bound GKRP + GK has
% lower affinity for glucose (14mM) and is translocated in the
% nucleus.equation (glucokinase binding protein)
% So only the free GK in the cytosol is active. The binding of GKRP and GK
% is dependent on glucose, fructose and fructose-6p.
% No product inhibition of glucose_6p to the GK.
% Dependency on glucose and fructose_6p from 
%v2_deltag = -16.7;                          % [kJ/mol]
%v2_keq = keq(v2_deltag);                    
%v2_td = (glc*atp - glc6p*adp / v2_keq);

% Inhibition by GCRP
v2_n_gkrp = 2;
v2_km_glc1 = 15;         %[mM]
v2_km_fru6p = 0.010;     %[mM]
v2_b = 0.7;

v2_n = 1.6;
v2_km_glc = 7.5;            % [mM]
v2_km_atp = 0.26;           % [mM]
v2_Vmax = 25.2;

v2_gc_free = (glc^v2_n_gkrp / (glc^v2_n_gkrp + v2_km_glc1^v2_n_gkrp) ) * (1 - v2_b*fru6p/(fru6p + v2_km_fru6p));
v2 = scale_gly*v2_Vmax * v2_gc_free * atp/(v2_km_atp + atp) * glc^v2_n/(glc^v2_n + v2_km_glc^v2_n);

% *********************************** %
% v3 : D-Glucose-6-phosphate Phosphatase
% *********************************** %
% R00303_3.1.3.9_cyto
% D-Glucose-6-phosphate phosphohydrolase
% C00092 + C00001 <=> C00031 + C00009
% glucose_6P + H2O -> glucose + P
% Pubmed: PMID: 11879177 intracellular glucose-6-p concentration 0.05 - 1
% [Reczek1982, Arion1971, Nordlie1969]
%v3_deltag = -13.8;                          % [kJ/mol]
%v3_keq = keq(v3_deltag);                    
%v3_td = (glc6p - glc*p/v3_keq);
v3_km_glc6p = 2;    % [mM]
v3_Vmax =  18.9;

v3 = scale_gly * v3_Vmax * glc6p / (v3_km_glc6p + glc6p);

% *********************************** %
% v4 : D-Glucose-6-phosphate Isomerase
% *********************************** %
% R00771_5.3.1.9_cyto	D-Glucose-6-phosphate ketol-isomerase	C00092 <=> C00085	
% glucose_6P -> fructose_6P
%v4_deltag = 1.7;                          % [kJ/mol]
%v4_keq = keq(v4_deltag);                    
%v4_td = (glc6p - fru6p/v4_keq);

v4_keq = 0.517060817492925;
v4_km_glc6p  = 0.182;   % [mM]
v4_km_fru6p = 0.071;    % [mM]
v4_Vmax = 420;

v4 = scale_gly * v4_Vmax/v4_km_glc6p * (glc6p - fru6p/v4_keq) / (1 + glc6p/v4_km_glc6p + fru6p/v4_km_fru6p);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%   Glycogen metabolism               %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% *********************************** %
% v5 : Glucose 1-phosphate 1,6-phosphomutase
% *********************************** %
% R00959_5.4.2.2_cyto	
% alpha-D-Glucose 1-phosphate 1,6-phosphomutase	
% 1 C00103 <=> 1 C00092
% glucose_1p <-> glucose_6p
%
% Similar to other isomerases. Reversible only depending on Km for
% substrate, product and the Keq of the reaction.
% Find km values for the reaction !!!
% [Quick1974]
% The equilibrium lies strongly toward G6P (Keq ) 28
%or Keq ) 25),5,6 and the reaction proceeds through a ping-pong
%mechanism involving aspartyl-phosphoenzyme (PGMP) and
%-glucose-1,6-bisphosphate (G16BP) intermediates 
% [Kashiwaya1994]
%v5_deltag = -7.1;                          % [kJ/mol]
%v5_keq = keq(v5_deltag);                    
%v5_td = (glc1p - glc6p/v5_keq);

v5_keq = 15.717554082151441;
v5_km_glc6p  = 0.67;       % [mM]
v5_km_glc1p = 0.045;        % [mM]
v5_Vmax = 100;
v5 = scale_glyglc * v5_Vmax/v5_km_glc1p * (glc1p - glc6p/v5_keq) / (1 + glc1p/v5_km_glc1p + glc6p/v5_km_glc6p);

% *********************************** %
% v6 : UTP:Glucose-1-phosphate uridylyltransferase (UPGase)
% *********************************** %
% R00289_2.7.7.9_cyto	
% UTP:alpha-D-glucose-1-phosphate uridylyltransferase	
% C00075 + C00103 <=> C00013 + C00029																																																																																																																																																																																																																																																												
% UTP + glucose_1P <-> UDP_glucose + PP
% Compare the different measurements; integrate the UTP inhibition.
% [Chang1995, Enzymes of sugar activation, Turnquist1974]
% v6_deltag = 3.0;                          % [kJ/mol]
% v6_keq = keq(v6_deltag);                  % keq = 0.31 % 0.28 - 0.34                    
% v6_td = (utp * glc1p - udpglc * pp/v6_keq);

v6_keq = 0.312237619153088;
v6_km_utp = 0.563;       % mM   [ 0.200, 0.048]
v6_km_glc1p = 0.172;     % mM [0.050, 0.095]
v6_km_udpglc = 0.049;    % mM [0.060, 0.048]
v6_km_pp = 0.166;         % mM     [0.084, 0.210]
v6_Vmax = 80;
v6 = scale_glyglc * v6_Vmax/(v6_km_utp*v6_km_glc1p) * (utp * glc1p - udpglc * pp/v6_keq) / ( (1 + utp/v6_km_utp)*(1 + glc1p/v6_km_glc1p) + (1 + udpglc/v6_km_udpglc)*(1 + pp/v6_km_pp) - 1 );
            
% *********************************** %
% v7 : Pyrophosphate phosphohydrolase (PPase)
% *********************************** %
% R00004_3.6.1.1_cyto	
% Pyrophosphate phosphohydrolase	
% C00013 + C00001 <=> 2 C00009
% pp + h2o -> 2 p
% Low km for pp for very low pp concentations in the cell.
% much higher km value for human form 0.25 [Reichert1974]
%v7_deltag = -19.1;                          % [kJ/mol] [-19.2 Guyn1974]
%v7_keq = keq(v7_deltag);
%v7_td = (pp - p*p/v7_keq);
% Km [Tamura1980]

v7_km_pp = 0.005;
v7_Vmax = 2.4;

v7 = scale_glyglc * v7_Vmax * pp/(pp + v7_km_pp);

% *********************************** %
% v8 : Glycogen synthase (GS)
% *********************************** %
% P0001_cyto
% Glycogen synthase	
% udpglc -> udp + glycogen
% irreversible reaction

% x = [0 0.05 0.07 0.20 7.2] % mM glucose 6p
% D = [33 0 20 8.9 0.3] % Km values for udpglc Synthase D
% I = [1.5 1.1 0 0 0.2] % km values for udpglc Synthase I

% [1] hard glycogen capacity point
% The storage capacity of the hepatocyte for glycogen is limited.
% With increasing glycogen content the rate drops.
%v8_keq = keq(0);    % ! no data found, assumption of 0
%v8_td = (udpglc - udp*glyglc/v8_keq);

v8_C = 500;             % [mM] maximal storage capacity for glycogen per volume liver
v8_k1_max = 0.2;
v8_k1_nat = 0.224;
v8_k2_nat = 0.1504;
v8_k1_phospho = 3.003; 
v8_k2_phospho = 0.09029;
v8_Vmax =  13.2;

v8_storage_factor = (1+v8_k1_max) * (v8_C - glyglc)/( (v8_C - glyglc) + v8_k1_max * v8_C);
v8_k_udpglc_native = v8_k1_nat / (glc6p + v8_k2_nat);
v8_k_udpglc_phospho = v8_k1_phospho / (glc6p + v8_k2_phospho);
v8_native = scale_glyglc * v8_Vmax * v8_storage_factor * udpglc / (v8_k_udpglc_native + udpglc);
v8_phospho = scale_glyglc * v8_Vmax * v8_storage_factor * udpglc / (v8_k_udpglc_phospho + udpglc); 
v8 = (1 - gamma)* v8_native + gamma * v8_phospho;

% *********************************** %
% v9 : Glykogen-Phosphorylase (GP)
% *********************************** %
% v9	P0002_cyto	Glykogen-Phosphorylase	1 C90001 + 1 C00001 <=> 1 C00031																																																																																																																																																																																																																																																												
% glycogen + P -> glucose_1P
% Different regulation of the a Form (phosphorylated, active Form) and the 
% unphosphorylated native b-Form.
% [Lederer1976, Tan1975, Stalmans1981, Stalmans1975, Ercan-Fang2002,
% Maddaiah1966 ]
% v9_deltag = 4.0;                          % [kJ/mol]
% v9_keq = keq(v9_deltag);                  % (0.21 - 0.14)                      
% v9_td = (glyglc*p - glc1p/v9_keq);

v9_keq = 0.211826505793075;
v9_k_glyc_native = 4.8;     % [mM]  
v9_k_glyc_phospho = 2.7;    % [mM]  
v9_k_glc1p_native = 120;    % [mM]  
v9_k_glc1p_phospho = 2;     % [mM]
v9_k_p_native = 300;        % [mM]  
v9_k_p_phospho = 5;         % [mM]
v9_ki_glc_phospho = 5;      % [mM]
v9_ka_amp_native = 1;       % [mM]
v9_base_amp_native = 0.03;
v9_max_amp_native = 0.30;
v9_Vmax = 6.8;

v9_C = v8_C;             
v9_k1_max = v8_k1_max;
v9_fmax = (1+v9_k1_max) * glyglc /( glyglc + v9_k1_max * v9_C);
v9_vmax_native = scale_glyglc * v9_Vmax * v9_fmax * (v9_base_amp_native + (v9_max_amp_native - v9_base_amp_native) *amp/(amp+v9_ka_amp_native));
v9_native = v9_vmax_native/(v9_k_glyc_native*v9_k_p_native) * (glyglc*p - glc1p/v9_keq) / ( (1 + glyglc/v9_k_glyc_native)*(1 + p/v9_k_p_native) + (1 + glc1p/v9_k_glc1p_native)  - 1 );
v9_vmax_phospho = scale_glyglc * v9_Vmax * v9_fmax * exp(-log(2)/v9_ki_glc_phospho * glc);
v9_phospho = v9_vmax_phospho/(v9_k_glyc_phospho*v9_k_p_phospho) * (glyglc*p - glc1p/v9_keq) / ( (1 + glyglc/v9_k_glyc_phospho)*(1 + p/v9_k_p_phospho) + (1 + glc1p/v9_k_glc1p_phospho)  - 1 );
v9 = (1 - gamma) * v9_native + gamma * v9_phospho;

% *********************************** %
% v10 : Nucleoside-diphosphate kinase (ATP, GTP)
% *********************************** %
% ATP + GDP <-> ADP + GTP
% The concentrations of the nucleotides are coupled via the NDK reaction
% [Fukuchi1994, Kimura1988, Lam1986]
%v10_deltag = 0;        % [kJ/mol]  
%v10_keq = keq(v10_deltag); 
%v10_td = (atp*gdp - adp*gtp/v10_keq);

v10_keq = 1;
v10_km_atp = 1.33;       % [mM]
v10_km_adp = 0.042;      % [mM]
v10_km_gtp = 0.15;       % [mM]
v10_km_gdp = 0.031;      % [mM]
v10_Vmax = 0;

v10 = scale_gly * v10_Vmax / (v10_km_atp * v10_km_gdp) * (atp*gdp - adp*gtp/v10_keq) / ( (1 + atp/v10_km_atp)*(1 + gdp/v10_km_gdp) + (1 + adp/v10_km_adp)*(1 + gtp/v10_km_gtp) - 1);

% *********************************** %
% v11 : Nucleoside-diphosphate kinase (ATP, UTP)
% *********************************** %
% ATP + UDP <-> ADP + UTP
% [Fukuchi1994, Kimura1988, Lam1986]
%v11_deltag = 0;        % [kJ/mol]  
%v11_keq = keq(v11_deltag); 
%v11_td = (atp*udp - adp*utp/v11_keq);

v11_keq = 1;
v11_km_atp = 1.33;      % [mM]
v11_km_adp = 0.042;     % [mM]
v11_km_utp = 16;        % [mM]
v11_km_udp = 0.19;      % [mM]
v11_Vmax = 2940;

v11 = scale_glyglc * v11_Vmax / (v11_km_atp * v11_km_udp) * (atp*udp - adp*utp/v11_keq) / ( (1 + atp/v11_km_atp)*(1 + udp/v11_km_udp) + (1 + adp/v11_km_adp)*(1 + utp/v11_km_utp) - 1);

% *********************************** %
% v12 : ATP:AMP phosphotransferase (Adenylatkinase)
% *********************************** %
% v12	R00127_2.7.4.3_cyto	ATP:AMP phosphotransferase	C00002 + C00020 <=> 2 C00008
% ATP + AMP -> 2 ADP
%v12_deltag = 3.6;        % [kJ/mol]  
%v12_keq = keq(v12_deltag); 
%v12_td = (atp*amp - adp*adp/v12_keq);

v12_keq = 0.247390074904985;
v12_km_atp = 0.09;         % [mM]
v12_km_amp = 0.08;         % [mM]
v12_km_adp = 0.11;         % [mM]
v12_Vmax = 0;

v12 = scale_gly * v12_Vmax / (v12_km_atp * v12_km_amp) * (atp*amp - adp*adp/v12_keq) / ( (1+atp/v12_km_atp)*(1+amp/v12_km_amp) + (1+adp/v12_km_adp)*(1+adp/v12_km_adp) - 1); 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%   PFK / FBPase                      %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%   Bifunctional enzyme which is regulated by multiple effectors
%   - cAMP concentration, C++, 
%   - v14_vmax/v15_vmax kinase/phospatase = 90/22
%   Enzyme exist in phosphorylated and dephosphorylated form. The actual
%   kinetics is a combination of both enzyme forms depending on the 
%   phosphorylation state of the enzyme.

% *********************************** %
% v13 : PFK2
% *********************************** %
% v13	R02732_2.7.1.105_cyto	ATP:D-fructose-6-phosphate 2-phosphotransferase	1 C00002 + 1 C00085 <=> 1 C00008 + 1 C00665																																																																																																																																																																																																																																																												
% very sensitive to fructose6p, ATP not so important
% fru6p + atp -> fru26bp + adp
% Flux is combination of the both kinetics depending on the phosphorylation
% state
%v13_deltag = -14.2;                          % [kJ/mol]
%v13_keq = keq(v13_deltag);                    
%v13_td = (fru6p * atp - fru26bp * adp/v13_keq);

v13_n_native = 1.3;  
v13_n_phospho = 2.1;             
v13_k_fru6p_native = 0.016;      % [mM]
v13_k_fru6p_phospho = 0.050;     % [mM]
v13_k_atp_native = 0.28;         % [mM]
v13_k_atp_phospho = 0.65;        % [mM]
v13_Vmax =  0.0042;

v13_native = scale_gly * v13_Vmax * power(fru6p, v13_n_native) / (power(fru6p, v13_n_native) + power(v13_k_fru6p_native, v13_n_native)) * (atp / (atp + v13_k_atp_native));
v13_phospho = scale_gly * v13_Vmax * power(fru6p, v13_n_phospho) / (power(fru6p, v13_n_phospho) + power(v13_k_fru6p_phospho, v13_n_phospho)) * (atp / (atp + v13_k_atp_phospho));
v13 = (1 - gamma) * v13_native + gamma * v13_phospho;

% *********************************** %
% v14 : FBPase2
% *********************************** %
% v14	R02731_3.1.3.46_cyto	D-Fructose-2,6-bisphosphate 2-phosphohydrolase	1 C00665 + 1 C00001 <=> 1 C00085 + 1 C00009																																																																																																																																																																																																																																																												
% what kind of inhibition.
% fru26bp -> fru6p + p 
%v14_deltag = -16.3;                          % [kJ/mol]
%v14_keq = keq(v14_deltag);                    
%v14_td = (fru26bp - fru6p*p/v14_keq);

v14_km_fru26bp_native = 0.010;     %[mM]
v14_ki_fru6p_native = 0.0035;      %[mM]
v14_km_fru26bp_phospho = 0.0005;   %[mM]
v14_ki_fru6p_phospho = 0.010;      %[mM]
v14_Vmax =  0.126;

v14_native = scale_gly * v14_Vmax/(1 + fru6p/v14_ki_fru6p_native) * fru26bp / ( v14_km_fru26bp_native + fru26bp);
v14_phospho = scale_gly * v14_Vmax/(1 + fru6p/v14_ki_fru6p_phospho) * fru26bp / ( v14_km_fru26bp_phospho + fru26bp);
v14 = (1-gamma) * v14_native + gamma * v14_phospho;

% *********************************** %
% v15 : PFK1
% *********************************** %
% v15	R00756_2.7.1.11_cyto	ATP:D-fructose-6-phosphate 1-phosphotransferase	C00002 + C00085 <=> C00008 + C00354																																																																																																																																																																																																																																																												
% regulation with fructose_26P missing
% fru6p + atp -> fru16bp + adp
%v15_deltag = -14.2;                          % [kJ/mol]
%v15_keq = keq(v15_deltag);                    
%15_td = (fru6p*atp - fru16bp*atp/v15_keq);

v15_km_atp = 0.111;                % [mM] [b]
v15_km_fru6p = 0.077;              % [mM] [a]
v15_ki_fru6p = 0.012;              % [mM] [ai]
v15_ka_fru26bp = 0.001;            % [mM]
v15_Vmax = 7.182;

v15 = scale_gly * v15_Vmax * (1 - 1./(1 + fru26bp/v15_ka_fru26bp)) * fru6p*atp/(v15_ki_fru6p*v15_km_atp + v15_km_fru6p*atp + v15_km_atp*fru6p + atp*fru6p);

% *********************************** %
% v16 : FBP1
% *********************************** %
% v16	R00762_3.1.3.11_cyto	D-Fructose-1,6-bisphosphate 1-phosphohydrolase	C00354 + C00001 <=> C00085 + C00009																																																																																																																																																																																																																																																												
% has to be controlled.
% fru16bp + h2o -> fru6p + p
%v16_deltag = -16.3;                          % [kJ/mol]
%v16_keq = keq(v16_deltag);                    
%v16_td = (fru16bp - fru6p*p/v16_keq);

v16_ki_fru26bp = 0.001;               % [mM]
v16_km_fru16bp = 0.0013;              % [mM]
v16_Vmax = 4.326;
v16 = scale_gly * v16_Vmax / (1 + fru26bp/v16_ki_fru26bp) * fru16bp/(fru16bp + v16_km_fru16bp);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%   Downstream PFK                    %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% *********************************** %
% v17 : Aldolase
% *********************************** %
% v17	R01068_4.1.2.13_cyto	D-Fructose-1,6-bisphosphate D-glyceraldehyde-3-phosphate-lyase	C00354 <=> C00111 + C00118																																																																																																																																																																																																																																																												
% fru16bp -> grap + dhap
%v17_deltag = 23.8;                          % [kJ/mol]
%v17_keq = keq(v17_deltag); 
%v17_td = (fru16bp - grap*dhap/v17_keq);
% keq = 0.114;                 %[mM] erythrocyte

v17_keq = 9.762988973629690E-5;
v17_km_fru16bp = 0.0071;         %[mM]
v17_km_dhap = 0.0364;            %[mM]
v17_km_grap = 0.0071;            %[mM]
v17_ki1_grap = 0.0572;           %[mM]
v17_ki2_grap = 0.176;            %[mM]
v17_Vmax = 420;

v17 = scale_gly * v17_Vmax/v17_km_fru16bp * (fru16bp - grap*dhap/v17_keq) /(1 + fru16bp/v17_km_fru16bp + grap/v17_ki1_grap + dhap*(grap + v17_km_grap)/(v17_km_dhap*v17_ki1_grap) + (fru16bp*grap)/(v17_km_fru16bp*v17_ki2_grap));

% *********************************** %
% v18 : Triosephosphate Isomerase
% *********************************** %
% v18	R01015_5.3.1.1_cyto	D-Glyceraldehyde-3-phosphate ketol-isomerase	C00118 <=> C00111																																																																																																																																																																																																																																																												
% equilibrium far on side of the dhap
% dhap <-> grap
%v18_deltag = 7.5;                          % [kJ/mol]
% v18_keq = 0.0407;                %[mM] erythrocyte model
%v18_keq = keq(v18_deltag); 
%v18_td = (dhap - grap/v18_keq); 

v18_keq = 0.054476985386756;
v18_km_dhap = 0.59;             %[mM]
v18_km_grap = 0.42;             %[mM]
v18_Vmax = 420;

v18 = scale_gly * v18_Vmax/v18_km_dhap * (dhap - grap/v18_keq) / (1 + dhap/v18_km_dhap + grap/v18_km_grap);

% *********************************** %
% v19 : D-Glyceraldehyde-3-phosphate:NAD+ oxidoreductase (GAPDH)
% *********************************** %
% v19	R01061_1.2.1.12_cyto	D-Glyceraldehyde-3-phosphate:NAD+ oxidoreductase(phosphorylating)	C00118 + C00009 + C00003 <=> C00236 + C00004 + C00080																																																																																																																																																																																																																																																												
% grap + p + nad <-> bpg13 + nadh + h
%v19_deltag = 6.3;        % [kJ/mol]  
%v19_keq = keq(v19_deltag); 
%v19_keq = 0.000192;         % [mM]
%v19_td = ( nad * grap * p - bpg13*nadh/v19_keq); 

v19_keq = 0.086779866194594;
v19_k_nad = 0.05;        % [mM]
v19_k_grap = 0.005;      % [mM]
v19_k_p = 3.9;           % [mM]
v19_k_nadh = 0.0083;     % [mM]
v19_k_bpg13 = 0.0035;    % [mM]
v19_Vmax = 420;

v19 = scale_gly * v19_Vmax / (v19_k_nad*v19_k_grap*v19_k_p) * (nad*grap*p - bpg13*nadh/v19_keq) / ( (1 + nad/v19_k_nad) * (1+grap/v19_k_grap) * (1 + p/v19_k_p) + (1+nadh/v19_k_nadh)*(1+bpg13/v19_k_bpg13) - 1);

% *********************************** %
% v20 : Phosphoglycerate Kinase (PGK) ATP:3-phospho-D-glycerate 1-phosphotransferase
% *********************************** %
% v20	R01512_2.7.2.3_cyto	ATP:3-phospho-D-glycerate 1-phosphotransferase	C00002 + C00197 <=> C00008 + C00236																																																																																																																																																																																																																																																												
% adp + bpg13 -> atp + pg3
%v20_deltag = -18.5;        % [kJ/mol]  
%v20_deltag = -5;        % [kJ/mol]  
%v20_keq = keq(v20_deltag); 
%v20_keq = 1455;         % [mM] (1310)
%v20_td = (adp*bpg13 - atp*pg3/v20_keq); 

v20_keq = 6.958644052488538;
v20_k_adp = 0.35;       %[mM]
v20_k_atp = 0.48;       %[mM]
v20_k_bpg13 = 0.002;    %[mM]
v20_k_pg3 = 1.2;        %[mM]
v20_Vmax = 420;

v20 = scale_gly * v20_Vmax / (v20_k_adp*v20_k_bpg13) * (adp*bpg13 - atp*pg3/v20_keq) / ((1 + adp/v20_k_adp)*(1+bpg13/v20_k_bpg13) + (1+atp/v20_k_atp)*(1+pg3/v20_k_pg3) - 1); 

% *********************************** %
% v21 : 2-Phospho-D-glycerate 2,3-phosphomutase (PGM)
% *********************************** %
% v21	R01518_5.4.2.1_cyto	2-Phospho-D-glycerate 2,3-phosphomutase	C00631 <=> C00197																																																																																																																																																																																																																																																												
% pg3 <-> pg2
%v21_deltag = 4.4;        % [kJ/mol]  
%v21_keq = keq(v21_deltag); 
%v21_keq = 0.145;         % [mM] (0.1814)
%v21_td = (pg3 - pg2/v21_keq); 

v21_keq = 0.181375378837397;
v21_k_pg3 = 5;      % [mM]
v21_k_pg2 = 1;      % [mM]
v21_Vmax = 420;

v21 = scale_gly * v21_Vmax * (pg3 - pg2/v21_keq) / (pg3 + v21_k_pg3 *(1 + pg2/v21_k_pg2));

% *********************************** %
% v22 : 2-Phospho-D-glucerate hydro-lyase (enolase)
% *********************************** %
% v22	R00658_4.2.1.11_cyto	2-Phospho-D-glucerate hydro-lyase	C00631 <=> C00074 + C00001
% pg2 <-> pep
%v22_deltag = 7.5;        % [kJ/mol]  
%v22_keq = keq(v22_deltag); 
%v22_keq = 1.7;         % (0.0545)
%v22_td = (pg2 - pep/v22_keq); 

v22_keq = 0.054476985386756;
v22_k_pep = 1;      % [mM]
v22_k_pg2 = 1;      % [mM]
v22_Vmax = 35.994;

v22 = scale_gly * v22_Vmax * (pg2 - pep/v22_keq) / (pg2 + v22_k_pg2 *(1 + pep/v22_k_pep));

% *********************************** %
% v23 : Pyruvatkinase (PK)
% *********************************** %
% v23	R00200_2.7.1.40_cyto	ATP:pyruvate O2-phosphotransferase	C00002 + C00022 <=> C00008 + C00074																																																																																																																																																																																																																																																												
%v23_deltag = -31.4;        % [kJ/mol]  
%v23_keq = keq(v23_deltag);
%v23_td = (pep*adp - atp*pyr/v23_keq);            

v23_n = 3.5;
v23_n_p = 3.5;
v23_n_fbp = 1.8;
v23_n_fbp_p = 1.8;
v23_alpha = 1.0;  
v23_alpha_p = 1.1;
v23_alpha_end = 1.0;
v23_k_fbp = 0.16E-3;
v23_k_fbp_p = 0.35E-3;
v23_k_pep = 0.58;
v23_k_pep_p = 1.10;
v23_k_pep_end = 0.08;
v23_k_adp = 2.3;        % [mM]
v23_base_act = 0.08;
v23_base_act_p = 0.04;
v23_Vmax = 46.2;

v23_f = fru16bp^v23_n_fbp / (v23_k_fbp^v23_n_fbp + fru16bp^v23_n_fbp);
v23_f_p = fru16bp^v23_n_fbp_p / (v23_k_fbp_p^v23_n_fbp_p + fru16bp^v23_n_fbp_p);
v23_alpha_inp = (1 - v23_f) * (v23_alpha - v23_alpha_end) + v23_alpha_end;
v23_alpha_p_inp = (1 - v23_f_p) * (v23_alpha_p - v23_alpha_end) + v23_alpha_end;
v23_pep_inp = (1 - v23_f) * (v23_k_pep - v23_k_pep_end) + v23_k_pep_end;
v23_pep_p_inp = (1 - v23_f_p) * (v23_k_pep_p - v23_k_pep_end) + v23_k_pep_end;
v23_native =  scale_gly * v23_Vmax * v23_alpha_inp * pep^v23_n/(v23_pep_inp.^v23_n + pep^v23_n) * adp/(adp + v23_k_adp) * ( v23_base_act + (1-v23_base_act) *v23_f );
v23_phospho = scale_gly * v23_Vmax * v23_alpha_p_inp * pep^v23_n_p/(v23_pep_p_inp.^v23_n_p + pep^v23_n_p) * adp/(adp + v23_k_adp) * ( v23_base_act_p + (1-v23_base_act_p) * v23_f_p );
v23 = (1-gamma)* v23_native + gamma * v23_phospho;

% *********************************** %
% v24 : PEPCK
% *********************************** %
% Michaelis-Menten Kinetics
% mitochondrial PEPCK has very similar Kinetics
% [Yang2009, Case2007]
% oxalacetate + GTP -> PEP + GDP + CO2
%v24_deltag = -15;        % [kJ/mol]  
%v24_keq = keq(v24_deltag); % 337 [mM]
%v24_td = ( oaa * gtp - pep*gdp*co2/v24_keq); 

v24_keq = 3.369565215864287E2;
v24_k_pep = 0.237;
v24_k_gdp = 0.0921;
v24_k_co2 = 25.5;
v24_k_oaa = 0.0055;
v24_k_gtp = 0.0222;
v24_Vmax = 0;

v24 = scale_gly * v24_Vmax / (v24_k_oaa * v24_k_gtp) * (oaa*gtp - pep*gdp*co2/v24_keq) / ( (1+oaa/v24_k_oaa)*(1+gtp/v24_k_gtp) + (1+pep/v24_k_pep)*(1+gdp/v24_k_gdp)*(1+co2/v24_k_co2) - 1 );

% *********************************** %
% v25 : PEPCK mito
% *********************************** %
% v25_td = (oaa_mito * gtp_mito - pep_mito*gdp_mito*co2_mito /v24_keq); 
v25_Vmax = 546;

v25 = scale_gly * v25_Vmax / (v24_k_oaa * v24_k_gtp) * (oaa_mito*gtp_mito - pep_mito*gdp_mito*co2_mito /v24_keq) / ( (1+oaa_mito/v24_k_oaa)*(1+gtp_mito/v24_k_gtp) + (1+pep_mito/v24_k_pep)*(1+gdp_mito/v24_k_gdp)*(1+co2_mito/v24_k_co2) - 1 );

% *********************************** %
% v26 : Pyruvate Carboxylase
% *********************************** %
% Acetyl-CoA is allosterical activator.
% [Jitrapakdee1999, Scrutton1974]
% Irreversible reaction
% atp + pyr + co2 -> oaa + adp + p
%v26_deltag = 0;                 % ??? [kJ/mol]  
%v26_keq = keq(v26_deltag); 
%v26_td = (atp_mito*pyr_mito*co2_mito - oaa_mito*adp_mito*p_mito/v26_keq); 

v26_k_atp = 0.22;  %[mM]
v26_k_pyr = 0.22;  %[mM]
v26_k_co2 = 3.2;   %[mM]
v26_k_acoa = 0.015; %[mM]
v26_n = 2.5;
v26_Vmax = 168;

v26 = scale_gly * v26_Vmax * atp_mito/(v26_k_atp + atp_mito) * pyr_mito/(v26_k_pyr + pyr_mito) * co2_mito/(v26_k_co2 + co2_mito) * acoa_mito^v26_n / (acoa_mito^v26_n + v26_k_acoa^v26_n);

% *********************************** %
% v27 : Lactate Dehydrogenase
% *********************************** %
% pyr + nadh <-> lac + nad 
%v27_deltag = 21.1;        % [kJ/mol]  
%v27_keq = keq(v27_deltag); 
%v27_td = (pyr*nadh - lac*nad/v27_keq);

v27_keq = 2.783210760047520e-004;
v27_k_pyr = 0.495;      % [mM]
v27_k_lac = 31.98;      % [mM]
v27_k_nad = 0.984;      % [mM]
v27_k_nadh = 0.027;      % [mM]
v27_Vmax = 12.6;

v27 = scale_gly * v27_Vmax / (v27_k_pyr * v27_k_nadh) * (pyr*nadh - lac*nad/v27_keq) / ( (1+nadh/v27_k_nadh)*(1+pyr/v27_k_pyr) + (1+lac/v27_k_lac) * (1+nad/v27_k_nad) - 1);

% *********************************** %
% v28 : Lactate Transport (import)
% *********************************** %
% high capacity importer
% lactate_ext -> lactate
%v28_deltag = 0;
%v28_keq = keq(v28_deltag);
%v28_td = (lac_ext - lac/v28_keq);

v28_keq = 1;
v28_k_lac = 0.8;                % [mM]
v28_Vmax = 5.418;

v28 = scale_gly * v28_Vmax/v28_k_lac * (lac_ext - lac/v28_keq) / (1 + lac_ext/v28_k_lac + lac/v28_k_lac);

% *********************************** %
% v29 : Pyruvate Transport (import mito)
% *********************************** %
%v29_deltag = 0;
%v29_keq = keq(v29_deltag);
%v29_td = (pyr - pyr_mito/v29_keq);

v29_keq = 1;
v29_k_pyr = 0.1;                % [mM]
v29_Vmax = 42;

v29 = scale_gly * v29_Vmax/v29_k_pyr * (pyr - pyr_mito/v29_keq) / (1 + pyr/v29_k_pyr + pyr_mito/v29_k_pyr);

% *********************************** %
% v30 : PEP Transport (export mito)
% *********************************** %
%v30_deltag = 0;
%v30_keq = keq(v30_deltag);
%v30_td = (pep_mito - pep/v30_keq);

v30_keq = 1;
v30_k_pep = 0.1;                % [mM]
v30_Vmax = 33.6;

v30 = scale_gly * v30_Vmax/v30_k_pep * (pep_mito - pep/v30_keq) / (1 + pep/v30_k_pep + pep_mito/v30_k_pep);

% *********************************** %
% v31 : PDH
% *********************************** %
% reaction is irreversibel
% PDH regulated by phosphorylation, dephosphorylation mechanism
% phosphorylated form is not very active
% unphosphorylated form is more active
% pyr + coa + nad -> acoa + co2 + nadh + h
% [Hamada1975, Korotchkina2006, Kiselevsky1990, Holness1988]
%v31_keq = 1;
%v31_td = (pyr_mito*coa_mito*nad_mito - acoa_mito*co2_mito*nadh_mito/v31_keq);

v31_k_pyr = 0.025;           % [mM] 
v31_k_coa = 0.013;           % [mM]
v31_k_nad = 0.050;           % [mM] 
v31_ki_acoa = 0.035;         % [mM]
v31_ki_nadh = 0.036;
v31_alpha_nat = 5;
v31_alpha_p = 1;
v31_Vmax = 13.44;

v31_base = scale_gly * v31_Vmax * pyr_mito/(pyr_mito + v31_k_pyr) * nad_mito/(nad_mito + v31_k_nad*(1 + nadh_mito/v31_ki_nadh)) * coa_mito/(coa_mito + v31_k_coa*(1+acoa_mito/v31_ki_acoa));
v31_nat = v31_base * v31_alpha_nat;
v31_p = v31_base * v31_alpha_p;
v31 = (1 - gamma) * v31_nat + gamma * v31_p;

% *********************************** %
% v32 : CS
% *********************************** %
% acoa_mito + oaa_mito + h2o mito -> cit_mito + coa_mito
% ATP inhibition not integrated
% [Shepherd1969, Smitherman1979, Matsuoka1973, Nelson2008]
%v32_deltag = -32.2;        % [kJ/mol]  
%v32_keq = keq(v32_deltag); 
%v32_td = (acoa_mito * oaa_mito - cit_mito*coa_mito/v32_keq);

v32_keq = 2.665990308427589e+005;
v32_k_oaa = 0.002;           % [mM] 
v32_k_acoa = 0.016;          % [mM]
v32_k_cit = 0.420;           % [mM] 
v32_k_coa = 0.070;           % [mM]
v32_Vmax = 4.2;

v32 = scale_gly * v32_Vmax/(v32_k_oaa * v32_k_acoa) * (acoa_mito*oaa_mito - cit_mito*coa_mito/v32_keq) / ( (1+acoa_mito/v32_k_acoa)*(1+oaa_mito/v32_k_oaa) + (1+cit_mito/v32_k_cit)*(1+coa_mito/v32_k_coa) -1 );

% *********************************** %
% v33 : Nucleoside-diphosphate kinase (ATP, GTP)
% *********************************** %
% ATP + GDP <-> ADP + GTP
% The concentrations of the nucleotides are coupled via the NDK reaction
% [Fukuchi1994, Kimura1988, Lam1986]
%v33_deltag = 0;        % [kJ/mol]  
%v33_keq = keq(v33_deltag); 
%v33_td = (atp_mito*gdp_mito - adp_mito*gtp_mito/v33_keq);

v33_keq = 1;
v33_k_atp = 1.33;       % [mM]
v33_k_adp = 0.042;      % [mM]
v33_k_gtp = 0.15;       % [mM]
v33_k_gdp = 0.031;      % [mM]
v33_Vmax = 420;

v33 = scale_gly * v33_Vmax / (v33_k_atp * v33_k_gdp) * (atp_mito*gdp_mito - adp_mito*gtp_mito/v33_keq) / ( (1 + atp_mito/v33_k_atp)*(1 + gdp_mito/v33_k_gdp) + (1 + adp_mito/v33_k_adp)*(1 + gtp_mito/v33_k_gtp) - 1) ;

% *********************************** %
% v34 : OAA influx
% *********************************** %
v34_Vmax = 0;
v34 = scale_gly * v34_Vmax;

% *********************************** %
% v35 : Acetyl-CoA efflux
% *********************************** %
v35_Vmax = 0;
v35 = scale_gly * v35_Vmax;

% *********************************** %
% v36 : Citrate efflux
% *********************************** %
v36_Vmax = 0;
v36 = scale_gly * v36_Vmax;


%%  Fluxes and concentration changes
dydt = zeros(size(y));
dydt(1) = 0;    % -v2 -v10 -v11 -v12 -v13 -v15 +v20 +v23;     %atp
dydt(2) = 0;    % +v2 +v10 +v11 +2*v12 +v13 +v15 -v20 -v23;   %adp
dydt(3) = 0;    % -v12;         %amp
dydt(4) = -v6 +v11;     %utp
dydt(5) = +v8 -v11;     %udp
dydt(6) = +v10 -v24;    %gtp
dydt(7) = -v10 +v24;    %gdp
dydt(8) = 0;    % -v19 +v27;    %nad
dydt(9) = 0;    % +v19 -v27;    %nadh
dydt(10) = 0;   % +v3 +2*v7 -v9 +v14 +v16 -v19;   %p
dydt(11) = +v6 -v7;     %pp
dydt(12) = 0;   % -v3 -v7 -v14 -v16 +v22;   %h2o
dydt(13) = 0;   % +v24;        %co2
dydt(14) = 0;   % +v19 -v27;   %h
dydt(15) = -v5 -v6 +v9; %glc1p
dydt(16) = +v6 -v8;     %udpglc
dydt(17) = +v8 -v9;     %glyglc
dydt(18) = +v1 -v2 +v3; %glc
dydt(19) = +v2 -v3 -v4 +v5;   %glc6p
dydt(20) = +v4 -v13 +v14 -v15 +v16;   %fru6p
dydt(21) = +v15 -v16 -v17;   %fru16bp
dydt(22) = +v13 -v14;           %fru26bp
dydt(23) = +v17 +v18 -v19;   %grap
dydt(24) = +v17 -v18;   %dhap
dydt(25) = +v19 -v20;   %bpg13
dydt(26) = +v20 -v21;   %pg3
dydt(27) = +v21 -v22;   %pg2
dydt(28) = +v22 -v23 +v24 +v30;   %pep
dydt(29) = +v23 -v27 -v29;   %pyr
dydt(30) = -v24;   %oaa
dydt(31) = +v27 +v28;   %lac
dydt(32) = 0;   % -v1;   %glc_{ext}
dydt(33) = 0;   % -v28;   %lac_{ext}
dydt(34) = 0;   % +5*v25 -5*v26 +5*v31;   %co2_{mito}
dydt(35) = 0;   % +5*v26;   %p_{mito}
dydt(36) = -5*v25 +5*v26 -5*v32 +5*v34;   %oaa_{mito}
dydt(37) = +5*v25 -5*v30;   %pep_{mito}
dydt(38) = 0;   % +5*v31 -5*v32 -5*v35;   %acoa_{mito}
dydt(39) = -5*v26 +5*v29 -5*v31;   %pyr_{mito}
dydt(40) = 0;   % +5*v32 -5*v36;   %cit_{mito}
dydt(41) = 0;   % -5*v26 -5*v33;   %atp_{mito}
dydt(42) = 0;   % +5*v26 +5*v33;   %adp_{mito}
dydt(43) = -5*v25 +5*v33;   %gtp_{mito}
dydt(44) = +5*v25 -5*v33;   %gdp_{mito}
dydt(45) = 0;   % -5*v31 +5*v32;   %coa_{mito}
dydt(46) = 0;   % +5*v25 +5*v31;   %nadh_{mito}
dydt(47) = 0;   % +5*v25 -5*v31;   %nad_{mito}
dydt(48) = 0;   % +5*v25 +5*v31;   %h_{mito}
dydt(49) = 0;   % -5*v32;   %h2o_{mito}

global glycogen_constant
if (exist('glycogen_constant', 'var') && isequal(glycogen_constant,1) )
    dydt(17) = 0;
end



%% Actual fluxes
v  = [v1 v2 v3 v4 v5 v6 v7 v8 v9 v10 v11 v12 v13 v14 v15 v16 v17 v18 v19 v20 v21 v22 v23 v24 v25 v26 v27 v28 v29 v30 v31 v32 v33 v34 v35 v36]';
%{
stoichiometry = model_stoichiometry(); 
dydt = stoichiometry * v;
const = [
    1       % 'atp'
    2       % 'adp'
    3       % 'amp'
    8       % 'nad'
    9       % 'nadh'
    10      % 'p' 
    12      % 'h20' 
    13      % 'co2'
    14      % 'h'   
    17      % 'glyglc'   
    32      % 'glc_ext'
    33      % 'lac_ext'
    34      % 'co2_mito' 
    35      % 'p_mito'
    38      % 'acoa_mito'
    40      % 'cit_mito'
    41      % 'atp_mito' 
    42      % 'adp_mito'
    45      % 'coa_mito'
    46      % 'nadh_mito' 
    47      % 'nad_mito' 
    48      % 'h_mito'
    49      % 'h2o_mito' 
];
dydt(const) = 0;
%}

