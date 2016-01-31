a
a.b
a()
a(1)
a{1}
a.b.c
a{1}{2}
% FIXME currently fails:
%a.b{1}{2}()
% FIXME currently fails:
%a.b{1}{2}(3)

a.b = 1
a(1).b = 1
a{1}.b = 1
a.c.b = 1

% FIXME currently fails:
%q(1).b{1}(1)
