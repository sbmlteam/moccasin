function valid_57(x)
   y = 1.5*cos(x) + 6*exp(-.1*x) + exp(.07*x).*sin(3*x);
   ym = mean(y);
   hfig = figure('Name','Function and Mean');
   hax = axes('Parent',hfig);
   plot(hax,x,y)
   hold on
   plot(hax,[min(x) max(x)],[ym ym],'Color','red')
   hold off
   ylab = hax.YTick;
   new_ylab = sort([ylab, ym]);
   hax.YTick = new_ylab;
   title ('y = 1.5cos(x) + 6e^{-0.1x} + e^{0.07x}sin(3x)')
   xlabel('X Axis')
   ylabel('Y Axis')
end