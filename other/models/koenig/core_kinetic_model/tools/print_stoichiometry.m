% print the stoichiometric matrix
N = model_stoichiometry(); 

% print all the rows
[Nx, Nv] = size(N);
names_x = names_s();
names_v = names_v();
linesep = '---------------------';

disp(linesep);
for kv=1:Nv
   disp(sprintf(' # v%s : %s #', num2str(kv), names_v{kv}));
   for kx=1:Nx
       sval = N(kx, kv);
       if (sval ~= 0)
          s = sprintf('%s [%s] %s ', num2str(sval), num2str(kx), names_x{kx});
          disp(s);
       end
   end
   disp(linesep);
end

disp(linesep);
for kx=1:Nx
   % disp(sprintf(' # %s : %s #', num2str(kx), names_x{kx}));
   s = sprintf('dydt(%d) = ', kx);
   for kv=1:Nv
       
       sval = N(kx, kv);
       if (sval ~= 0)
            if (sval == 1)
                s = strcat(s, sprintf(' +v%d', kv));
            elseif (sval == -1)
                s = strcat(s, sprintf(' -v%d', kv));
            else
                s = strcat(s, sprintf(' %+d*v%d', sval, kv));
            end
       end
   end
   s = strcat(s, ';   % ', num2str(names_x{kx}));
   disp(s);
   % disp(linesep);
end
disp(linesep);
