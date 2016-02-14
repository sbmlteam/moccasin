function A(x, y)              % Main function
B(x,y)
D(y)

   function B(x,y)            % Nested in A
   C(x)
   D(y)

      function C(x)           % Nested in B
      D(x)
      end
   end

   function D(x)              % Nested in A
   E(x)

      function E(x)           % Nested in D
      disp(x)
      end
   end

end
