t=(0:0.001:1);
plot(t,sin(2*pi*[t ; t+0.25]));
xlabel('t'); 
ylabel('$\hat{y}_k=sin 2\pi (t+{k \over 4})$','Interpreter','latex');
legend({'$\hat{y}_0$','$\hat{y}_1$'},'Interpreter','latex');
