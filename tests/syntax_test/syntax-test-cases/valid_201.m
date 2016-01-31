(a || b).'
(a || b) .^ c
(a || b)'
(a || b) ^ c

+a.'
+b.^c
+d'
+e^f

-a.'
-b.^c
-d'
-e^f

~a.'
~b.^c
~d'
~e^f

+a .* b
-a .* b
~a .* b

+a ./ b
-a ./ b
~a ./ b

+a .\ b
-a .\ b
~a .\ b

+a * b
-a * b
~a * b

+a / b
-a / b
~a / b

+a \ b
-a \ b
~a \ b

a + b : c + d
a + b : c + d : e + f

% FIXME: next two are parsed incorrectly as a command-style function call:
% FIXME: uncomment when parser is fixed.
% a - b : c - d
% a - b : c - d : e - f

a : b < c : d
a : b > c : d
a : b <= c : d
a : b >= c : d

a < b & c < d
a > b & c > d
a <= b & c <= d
a >= b & c >= d
