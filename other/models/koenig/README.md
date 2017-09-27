This was a model provided by Matthias König at Computational Systems Biochemistry Group, Charité - Universitätsmedizin Berlin.

He gave the following explanation/instructions:

Find attached a matlab model with the ODEs in `dydt_glucose_model_sbml.m`. I also attached the SBML for the model.

Special tricks I do 

1. is mainly writing the units of my values as direct comments behind the values (which makes it easy to parse afterwards) and 
1. provide multiple return values from the ode to get additional parameters I define in the ODEs.

The model was already rewritten to make it easy to transform in SBML (i.e. no more matrix operations and trying to not use matlab build in functions like (min, max, ...) (so somehow a biased example).

`sim_single.m` starts a single simulation
