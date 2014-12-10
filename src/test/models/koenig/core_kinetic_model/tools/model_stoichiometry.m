function N = model_stoichiometry()
%% MODEL_STOICHIOMETRY stoichiometric matrix of the system
%
%   Returns:
%       N:  stoichiometric matrix of the system
%
%   author: Matthias Koenig 
%   date:   110211


% Verhältnisse der Compartments
a = 5;    % V_cyto/V_mito
b = 1;    % V_cyto/V_blood    

% Stoichiometric matrix of the model.
%        v1   v2   v3   v4   v5   v6   v7   v8   v9   v10  v11  v12  v13  v14  v15  v16  v17  v18  v19  v20  v21  v22  v23  v24  v25  v26  v27 v28 v29  v30 v31 v32 v33 v34 v35 v36 
  N = [  0   -1    0    0    0    0    0    0    0   -1   -1   -1   -1    0   -1    0    0    0    0    1    0    0    1    0    0    0    0    0   0   0   0   0   0   0   0   0    % atp
         0    1    0    0    0    0    0    0    0    1    1    2    1    0    1    0    0    0    0   -1    0    0   -1    0    0    0    0    0   0   0   0   0   0   0   0   0    % adp
         0    0    0    0    0    0    0    0    0    0    0   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % amp
         0    0    0    0    0   -1    0    0    0    0    1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % utp
         0    0    0    0    0    0    0    1    0    0   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % udp
         0    0    0    0    0    0    0    0    0    1    0    0    0    0    0    0    0    0    0    0    0    0    0   -1    0    0    0    0   0   0   0   0   0   0   0   0    % gtp
         0    0    0    0    0    0    0    0    0   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    1    0    0    0    0   0   0   0   0   0   0   0   0    % gdp
         
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -1    0    0    0    0    0    0    0    1    0   0   0   0   0   0   0   0   0    % nad
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1    0    0    0    0    0    0    0   -1    0   0   0   0   0   0   0   0   0    % nadh

         0    0    1    0    0    0    2    0   -1    0    0    0    0    1    0    1    0    0   -1    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % p
         0    0    0    0    0    1   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % pp
         0    0   -1    0    0    0   -1    0    0    0    0    0    0   -1    0   -1    0    0    0    0    0    1    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % h2o
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1    0    0    0    0   0   0   0   0   0   0   0   0    % co2 
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1    0    0    0    0    0    0    0   -1    0   0   0   0   0   0   0   0   0    % h
         
         0    0    0    0   -1   -1    0    0    1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % glc1p
         0    0    0    0    0    1    0   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % udpglc
         0    0    0    0    0    0    0    1   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % glyglc
         
         1   -1    1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % glc
         0    1   -1   -1    1    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % glc6p
         0    0    0    1    0    0    0    0    0    0    0    0   -1    1   -1    1    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % fru6p
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    1   -1   -1    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % fru16bp
         0    0    0    0    0    0    0    0    0    0    0    0    1   -1    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % fru26bp
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1    1   -1    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % grap
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1   -1    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % dhap
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1   -1    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % bpg13
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1   -1    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % pg3
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1   -1    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % pg2
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1   -1    1    0    0    0    0   0   1   0   0   0   0   0   0    % pep
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1    0    0    0   -1    0  -1   0   0   0   0   0   0   0    % pyr
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -1    0    0    0    0   0   0   0   0   0   0   0   0    % oaa 
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    1    1   0   0   0   0   0   0   0   0    % lac  
         
        -b    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   0   0   0   0   0    % glc_ext
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -b   0   0   0   0   0   0   0   0    % lac_ext
         
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a   -a    0    0   0   0   a   0   0   0   0   0    % co2_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0   0   0   0   0   0   0   0   0    % p_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -a    a    0    0   0   0   0  -a   0   a   0   0    % oaa_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0    0   0  -a   0   0   0   0   0   0    % pep_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   a  -a   0   0  -a   0    % acoa_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -a    0    0   a   0  -a   0   0   0   0   0    % pyr_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0   a   0   0   0  -a    % cit_mito
         
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -a    0    0   0   0   0   0  -a   0   0   0    % atp_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0   0   0   0   0   a   0   0   0    % adp_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   -a    0    0    0   0   0   0   0   a   0   0   0    % gtp_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0    0   0   0   0   0  -a   0   0   0    % gdp_mito
         
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0  -a   a   0   0   0   0    % coa_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0    0   0   0   a   0   0   0   0   0    % nadh_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0    0   0   0  -a   0   0   0   0   0    % nad_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    a    0    0    0   0   0   a   0   0   0   0   0    % h_mito
         0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0    0   0   0   0  -a   0   0   0   0    % h2o_mito
        
%        v1   v2   v3   v4   v5   v6   v7   v8   v9   v10  v11 v12  v13  v14  v15  v16  v17  v18  v19  v20  v21  v22  v23  v24  v25  v26 v27  v28  v29 v30 v31 v32 v33 v34 v35 v36
     ];


 
 
% v1 : GLUT2        1 glucose_ext <-> 1 glucose
% v2 : GK           1 atp + 1 glc -> 1 adp + 1 glc6p
% v3 : G6Pase       1 glc6p + 1 h2o -> 1 glc + 1 p
% v4 : GPI          1 glc6p <-> fru6p
% v5 : G16PI        1 glc1p <-> 1 glc6p
% v6 : UPGase       1 glc1p + utp <-> 1 udpglc + pp
% v7 : PPase        1 pp + 1 h2o -> 2 p
% v8 : Glycogen synthase            1 udpglc + 1 udp -> 1 glyglc
% v9 : Glycogen phosphorylase       1 glyglc + 1 p <-> 1 glc1p
% v10: NTK (GTP)    1 atp + 1 gdp <-> 1 adp + 1 gtp
% v11: NTK (UTP)    1 atp + 1 udp <-> 1 adp + 1 utp
% v12: AK           1 atp + 1 amp <-> 2 adp
% v13: PFK2         1 atp + 1 fru6p -> 1 adp + 1 fru26bp
% v14: FBP2         1 fru26bp + 1 h2o -> 1 p + 1 fru6p
% v15: PFK1         1 atp + 1 fru6p -> 1 adp + 1 fru16bp
% v16: FBP1         1 fru16bp + 1 h2o -> 1 p + 1 fru6p
% v17 : ALD         1 fru16bp <-> 1 dhap + 1 grap
% v18 : TPI         1 dhap <-> 1 grap
% v19 : GAPDH       1 grap + 1 p + 1 nad <-> 1 nadh + 1 h + 1 bpg13
% v20 : PGK         1 adp + 1 bpg13 <-> 1 atp + pg3
% v21 : PGM         1 pg3 <-> 1 pg2
% v22 : Enolase     1 pg2 <-> 1 pep + 1 h2o
% v23 : PK          1 adp + 1 pep -> 1 atp + 1 pyr
% v24 : PEPCK       1 oaa + 1 gtp <-> 1 pep + 1 gdp + 1 co2
% v25 : PEPCK_mito  1 oaa_mito + 1 gtp_mito <-> 1 pep_mito + 1 gdp_mito + 1 co2_mito
% v26 : PC          1 pyr_mito + 1 atp_mito + 1 co2_mito -> 1 oaa_mito + 1 adp_mito + 1 p_mito
% v27 : LDH         1 pyr + 1 nadh + 1 h <-> 1 lac + 1 nad
% v28 : LacT        1 lac_ext <-> 1 lac
% v29 : PyrT        1 pyr -> 1 pyr_mito 
% v30 : PepT        1 pep_mito -> 1 pep
% v31 : PDH         1 pyr_mito + 1 coa_mito + 1 nad_mito -> 1 acoa_mito + 1 co2_mito + 1 nadh_mito + 1 h_mito
% v32 : CS          1 acoa_mito + 1 oaa_mito + 1 h2o mito -> 1 cit_mito + 1 coa_mito
% v33 : NDK         1 atp_mito + 1 gdp_mito -> 1 adp_mito + 1 gtp_mito
% v34 : OAAFLX      -> 1 oaa_mito
% v35 : ACOAFLX     1 acoa_mito -> 
% v36 : CITFLX      1 cit_mito ->


% S1 : atp
% S2 : adp
% S3 : amp
% S4 : utp
% S5 : udp
% S6 : gtp
% S7 : gdp

% S8 : nad
% S9 : nadh
% S10 : p
% S11 : pp
% S12 : h2o
% S13 : co2
% S14 : h

% S15 : glc1p
% S16 : udpglc
% S17 : glyglc

% S18 : glc
% S19 :  glc6p
% S20 :  fru6p
% S21 :  fru16bp
% S22 :  fru26bp
% S23 :  grap
% S24 :  dhap
% S25 :  bpg13
% S26 :  pg3
% S27 :  pg2
% S28 :  pep
% S29 :  pyr
% S30 :  oaa
% S31 :  lac
 
% S32 :  glc_ext
% S33 :  lac_ext
 
% S34 :  co2_mito
% S35 :  p_mito
% S36 :  oaa_mito
% S37 :  pep_mito
% S38 :  acoa_mito
% S39 :  pyr_mito
% S40 :  cit_mito
 
% S41 :  atp_mito
% S42 :  adp_mito
% S43 :  gtp_mito
% S44 :  gdp_mito

% S45 : coa_mito
% S46 : nadh_mito
% S47 : nad_mito
% S48 : h_mito
% S49 : h2o_mito
 