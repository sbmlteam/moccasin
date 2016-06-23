function x1 = run_cgs
    n = 21;
    b = afun(ones(n,1));
    tol = 1e-12; maxit = 15;
    x1 = cgs(@afun,b,tol,maxit,@mfun);
    function y = afun(x)
        y = [0; x(1:n-1)] + ...
            [((n-1)/2:-1:0)'; (1:(n-1)/2)'].*x + ...
            [x(2:n); 0];
    end
    function y = mfun(r)
        y = r ./ [((n-1)/2:-1:1)'; 1; (1:(n-1)/2)'];
    end
end