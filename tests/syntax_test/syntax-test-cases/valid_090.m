function [m,s] = valid_90(x)
n = length(x);
m = sum(x)/n;
s = sqrt(sum((x-m).^2/n));
end
