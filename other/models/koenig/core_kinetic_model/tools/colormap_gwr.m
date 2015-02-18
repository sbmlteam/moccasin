function [map] = colormap_gwr(x_min, x_max)
%COLORMAP_GWR Calculates a colormap with red to white for negative values
%  (min, 0) and red values for positive values (0,max).
%  min and max have to be values with only one decimal digit.
%  min has to be a negative value
%  max has to be a positive value

if ( round(10*x_min) ~= 10*x_min || round(10*x_max) ~= 10*x_max)
    error('min and max only one decimal digit')
end
if (x_min >= 0 || x_max <= 0)
   error('min >= 0 or max<=0') 
end
fac = 1;

N = fac*(x_max-x_min) + 1;
N_wg = fac * x_max + 1;
N_rw = - fac * x_min + 1;

map = ones(N, 3);
map(N_rw, :) = [0 0 0];

% Standard Map white -> green
map_setp = [1 251 501 751 1001];
map_wg_setvals = [ 1       1      1
                   0.6     0.8      0.6
                   0.2     0.6      0.2
                   0.14    0.3   0.14
                   0       0.05   0
                  ];
map_wg = createMap(map_setp, map_wg_setvals);
map_rw_setvals = [ 0.20       0      0
                   0.69     0.14      0.14
                   1     0.2      0.2
                   1    0.5   0.5
                    1       1   1
                  ];
map_rw = createMap(map_setp, map_rw_setvals);
%map = map_rw;

% Standard Map red -> white
%map_rw

% set rw part
for q = 1: N_rw
   round(q*1001/N_rw);
   map(q,:) = map_rw(max(round(q*1001/N_rw),1), :);
end
for q = 1 : N_wg
   round(q*1001/N_wg);
   map(N_rw + q,:) = map_wg(max(round(q*1001/N_wg),1), :);
end

function [map_ref] = createMap(setp, setvals)
    map_ref = zeros(map_setp(end), 3);
    % set reference colors
    for k=1:length(map_setp)
       index = setp(k);
       map_ref(k,:) = setvals(k, :); 
    end
    % interpolate between reference colors
    for k=1:length(setp)-1
       ref_1 = setvals(k, :);
       ref_2 = setvals(k+1, :);
       L = setp(k+1)-setp(k);
       m_1 = (ref_2 - ref_1)./L;
       for p=0:L
          map_ref(setp(k) + p,:) = setvals(k, :) + m_1 * p; 
       end
    end
end

end

