name = 'core_sbml'
switch (name)
    case 'core'
        % core model time in [min]
        dydt_fun = @(t,y) dydt_model_glucose(t,y);
    case 'core_sbml'
        % sbml model time in [s]
        dydt_fun = @(t,y) dydt_model_glucose_sbml(t,y);
        tspan = 60 * tspan;    % [s -> min]
        % v_full = 60 * v_full;  % [per_s] -> [per_min]
end
