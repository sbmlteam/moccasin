x = [12 64 24];
plottype = 'pie3';

switch plottype
    case 'bar' 
        bar(x)
        title('Bar Graph')
    case {'pie','pie3'}
        pie3(x)
        title('Pie Chart')
    otherwise
        warning('Unexpected plot type. No plot created.')
end
