a = @() 1
b = @(x) x
c = @(x, y) y - x
d = @(x, y) (y - x)
e = @(x, y) (@(x) x)
f = @(x)@(y) x + y
