function [ x0 ] = initial_concentrations(a)

% This syntax works:

x0 = [ 2.8000,
       0.8000, 
       0.1600  ];

% This fails:

x0 = [ 2.8000
       0.8000 
       0.1600  ];
end

