x = 1;
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

y = 2;
