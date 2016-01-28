p = fminsearch(@humps,.5)
exp_pdf = @(t)(1/mu1)*exp(-t/mu1);
