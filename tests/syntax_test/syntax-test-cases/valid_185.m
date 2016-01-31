function y = fcn1(x)
  y = 1;
end function [y] = fcn2(), y = 2;
end
function [y, z] = fcn3(a)
  y = a + 1;
  function q = fcn4
    q = 3
    %comment1
  end
  z = y; function r = fcn5
    %comment2
    r = 7
  end y = z;
end
function fcn6
  %%helpcomment1
end
%extracomment
