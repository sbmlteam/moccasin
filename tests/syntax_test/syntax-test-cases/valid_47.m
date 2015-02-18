z(:,p) = ( z_tmp(2:end, p) - z_tmp(1:end-1, p) )' ./ ( glc_ext(glc_min_ind+1:glc_max_ind) - glc_ext(1:glc_max_ind-1 ) );
