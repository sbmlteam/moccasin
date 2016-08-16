function [varargout]=resimmcode; 
%this Matlab script simulates the models described in: 
%"The role of the Immune Response in the Emergence of Antibiotic Resistance", Handel, Margolis, Levin
%one can simply run the model by calling [y]=resimmcode; 
%the data for the different models/scenarios is then saved in the files 'figdataX.mat' and can easily be plotted

clear all;
odeoptions = odeset('RelTol',1e-2,'AbsTol',1e-4); 

dvec0=datenum(now); %time at which simulation started

for ct=[5:8]  %loop over all different scenarios. Note that it includes some scenarios not used/shown in the paper
%for ct=[105:109]  %loop over MSW scenarios, with adherence. Note that it includes some scenarios not used/shown in the paper
%for ct=[210:214]  %loop over non-adhenrence scenarios. Note that it includes some scenarios not used/shown in the paper
%for ct=[314:318]  %loop over all different scenarios. Note that it includes some scenarios not used/shown in the paper
	dt=0.5; %datapoints at which to record solution 
   	tmax=(14+4)*24; %time is for now assumed to be in hours
   	mu=10^-8; %mutation rate
   	N0=10^9; %carrying capacity
   	tdrug=4*24; %drug treatment start
	tdosevec=24; %drug administration every 24h  
	gs=1; %growth rate of sensitive
    ks0=1.5; %max clearance of sensitive
	kr0=1.1; %max clearance of resistant
	Cs50=0.25; %1/2 level of sensitive
	Cr50=5; %1/2 level of resistant
	A0vec=4; %drug strength
    A0veclow=-2; A0vechigh=2;
	d=0.15; %drug decay rate
    %A0veclow=-4; A0vechigh=2; d=0.01; %alternatives for drug dynamics, not used in paper
    adhere=1; %drug is taken every time (adhere=2 means drug is taken every 2nd time, etc.)
	dp=48; %number of points for frequency, use 24 or 47 to get every 1h or 1/2h 
    dc=25; %number of points for concentration
	s=N0/100;
    dX=1/1;
    gX=dX/N0;
    I0=1e-6;
    Bs0=1e3;

	%this sets parameters for the different immune response terms
	if (ct==0), gr=0.65; s1=0; s2=0; gi=0; g2=0; b=0; filename='figdata0.mat'; end %no immune response

   	if (ct==1), gr=0.65; s1=1; s2=0; gi=1; g2=0; b=0.5; filename='figdata1a.mat'; end %model 1 response
	if (ct==2), gr=0.9;  s1=1; s2=0; gi=1; g2=0; b=0.5; filename='figdata1b.mat'; end %model 1 response

	if (ct==3), gr=0.65; s1=0; s2=1; gi=1; g2=0; b=0.5*s; filename='figdata2a.mat'; end %model 2 response
	if (ct==4), gr=0.9;  s1=0; s2=1; gi=1; g2=0; b=0.5*s*2; filename='figdata2b.mat'; end %model 2 response

	if (ct==5), gr=0.65; s1=1; s2=0; gi=0; g2=1; b=5; dX=1/4; gX=dX/N0;  filename='figdata3a.mat'; end %model 3 response
   	if (ct==6), gr=0.65; s1=1; s2=0; gi=0; g2=1; b=5; dX=1/20; gX=dX/N0; filename='figdata3b.mat'; end %model 3 response

   	if (ct==7), gr=0.65; s1=0; s2=1; gi=0; g2=1; b=5*s; dX=1/4; gX=dX/N0;  filename='figdata4a.mat'; end %model 4 response
   	if (ct==8), gr=0.65; s1=0; s2=1; gi=0; g2=1; b=5*s*2; dX=1/4; gX=dX/N0;  filename='figdata4b.mat'; end %model 4 response

   	if (ct==105), gr=0.65; s1=0; s2=0; gi=0; g2=0; b=0; dc=100; A0vec=logspace(A0veclow,A0vechigh,dc); filename='figdata5.mat'; end %no immune response, changing drug dosage, MSW
	if (ct==106), gr=0.65; s1=1; s2=0; gi=1; g2=0; b=0.5; dc=100; A0vec=logspace(-1,1,dc); filename='figdata6.mat'; end %model 1, changing dosage, MSW
	if (ct==107), gr=0.65; s1=0; s2=1; gi=1; g2=0; b=0.5*s*2; dc=100; A0vec=logspace(A0veclow,A0vechigh,dc); filename='figdata7.mat'; end %model 2, changing dosage, MSW
	if (ct==108), gr=0.65; s1=1; s2=0; gi=0; g2=1; b=5; dX=1/4; gX=dX/N0; dc=100; A0vec=logspace(-1,A0vechigh,dc); filename='figdata8.mat'; end %model 3, changing dosage, MSW 
	if (ct==109), gr=0.65; s1=0; s2=1; gi=0; g2=1; b=5*s*2; dX=1/4; gX=dX/N0; dc=100; A0vec=logspace(A0veclow,A0vechigh,dc); filename='figdata9.mat'; end %model 4, changing dosage, MSW 

    	if (ct==210), gr=0.65; s1=0; s2=0; gi=0; g2=0; b=0; dc=50; A0vec=logspace(-1.7,2,dc); adhere=2; filename='figdata10.mat'; end %no immune response, changing dosage, non-adherence
	if (ct==211), gr=0.65; s1=1; s2=0; gi=1; g2=0; b=0.5; dc=50; A0vec=logspace(-0.7,0.5,dc); adhere=2; filename='figdata11.mat'; end %model 1, changing dosage, non-adherence
	if (ct==212), gr=0.65; s1=0; s2=1; gi=1; g2=0; b=0.5*s*2; dc=40; A0vec=logspace(-2,0.5,dc); adhere=2; filename='figdata12.mat'; end %model 2, changing dosage, non-adherence
	if (ct==213), gr=0.65; s1=1; s2=0; gi=0; g2=1; b=5; dX=1/4; gX=dX/N0; dc=50; A0vec=logspace(-0.7,2,dc); adhere=2; filename='figdata13.mat'; end %model 3, changing dosage, non-adherence 
	if (ct==214), gr=0.65; s1=0; s2=1; gi=0; g2=1; b=5*s*2; dX=1/4; gX=dX/N0; dc=50; A0vec=logspace(-1.5,0.5,dc); adhere=2; filename='figdata14.mat'; end %model 3, changing dosage, non-adherence 
    	
	if (ct==314), gr=0.65; s1=0; s2=0; gi=0; g2=0; b=0; A0vec=10; tdosevec=linspace(48,1,dp); filename='figdata14.mat'; end %no immune response, changing dosing frequency
	if (ct==315), gr=0.65; s1=1; s2=0; gi=1; g2=0; b=0.5; A0vec=0.75; tdosevec=linspace(48,1,dp); filename='figdata15.mat'; end %model 1, changing dosing frequency
   	if (ct==316), gr=0.65; s1=0; s2=1; gi=1; g2=0; b=0.5*s*2; dc=50; A0vec=1.5; tdosevec=linspace(48,1,dp); filename='figdata16.mat'; end %model 2, saturated, changing dosing frequency
	if (ct==317), gr=0.65; s1=1; s2=0; gi=0; g2=1; b=5; dX=1/4; gX=dX/N0; A0vec=8; tdosevec=linspace(48,1,dp); filename='figdata17.mat'; end %model 3, changing dosing frequency 
	if (ct==318), gr=0.65; s1=0; s2=1; gi=0; g2=1; b=5*s*2; dX=1/4; gX=dX/N0; A0vec=2.5; tdosevec=linspace(48,1,dp); filename='figdata18.mat'; end %model 4, changing dosing frequency 

	ctt=1; %a counter
	avmax=1; %if adherence is perfect, everything is deterministic and we don't need to do Monte Carlo sampling
	if (adhere==2), avmax=5000; end %if adherence is probabilistic, we sample over 1000 infections

	%initialize array
	tinvade=zeros(avmax,length(tdosevec)*length(A0vec)); 

	%loop over either drug concentration or 
	for tdosing=tdosevec
		for A0=A0vec
			Adose=A0*tdosing/24; %normalize dose by dosing interval (A0 is total amount distributed over 24h)
			dvec=datevec(datenum(now)-dvec0);
			disp(sprintf('time passed h/m/s %d:%d:%d sec, start ct=%d, ctt=%d/%d, dosing interval=%d',round(dvec(4)),round(dvec(5)),round(dvec(6)),ct,ctt,length(tdosevec)*length(A0vec),tdosing));
			for avc=1:avmax    	
				%disp(sprintf('start ct=%d, ctt=%d/%d, infection run=%d/%d, dosing interval=%d',ct,ctt,length(tdosevec)*length(A0vec),avc,avmax,tdosing));
				y0=[Bs0; 0; I0; 0]; %initial values for [Bs Br I C] 
				t=0; 
				yvec=[]; tvec=[];  %initialize arrays
				[tvec1 yvec1]=ode45(@myode,[t:dt:tdrug],y0,odeoptions); %initial infection phase in absence of drug
				tvec=[tvec; tvec1]; yvec=[yvec; yvec1]; %save data 
				t=tdrug; y0=yvec(end,:); y0(4)=Adose; tpulse=t+tdosing; tpc=1; %start treatment
				while (t<tmax) %simulation of a single infection once treatment starts
					[tvec1 yvec1]=ode45(@myode,[t:dt:tpulse],y0,odeoptions); %integrate until next drug dose is administered
					tvec=[tvec; tvec1(2:end)]; yvec=[yvec; yvec1(2:end,:)]; %combine/save data
					t=tvec(end);
					yvec(yvec(:,1:2)<1)=0; %if it's less than one bacteria, set it to zero
					if (max(min(yvec(:,1:2)))<1 && ct>12), break; end %if no more sensitive or resistant bacteria are around, stop simulation
					y0=yvec(end,:); 
					if (adhere==1), y0(4)=y0(4)+Adose; %add new antibiotic dose Adose
					elseif (adhere==2), y0(4)=y0(4)+Adose*(rand<(0.25+ 0.75*log10(yvec(end,1)+yvec(end,2))/log10(N0))); end %non-adherence, add new dose with probability p
					tpulse=tpulse+tdosing; tpc=tpc+1; 
				end
				resind=min(find(yvec(:,2)>=N0/10)); %array index of the time when resistance emerged
				%sensfreq(avc,ctt)=yvec(end,1);
				%resfreq(avc,ctt)=yvec(end,2);
				if (sum(resind)==0), tinvade(avc,ctt)=inf; else tinvade(avc,ctt)=tvec(resind);  end  %if emergence did not occur, set to time to infinity, otherwise record time
			end %end avmax
            ctt=ctt+1;		
            
            	if (1==2)
			plot(tvec,yvec(:,1),'b');
			hold on;
			plot(tvec,yvec(:,2),'r');
			plot(tvec,yvec(:,3),'g');
			plot(tvec,yvec(:,4),'k');
			set(gca,'yscale','log');
			axis([0 tmax 1e-3 2e9]);
			drawnow;
			keyboard;
            	end
		end %end loop over different concentrations A0vec
	end %end loop over different dosing intervals tdosevec
%    keyboard;
    save(filename);
end %end ct loop
varargout{1}=ct; %dummy output

function dydt=myode(t,y)
	Bs=y(1); Br=y(2); X=y(3); C=y(4); %immune response is called X here
	N=Bs+Br; 
	ks=ks0*C/(C+Cs50); kr=kr0*C/(C+Cr50); %PD function
    dydt=[(1-mu)*gs*(1-N/N0)*Bs-ks*Bs-s1*b*X*Bs-s2*b*X*Bs/(s+N); 
         (1-N/N0)*(gs*mu*Bs+gr*Br)-kr*Br-s1*b*X*Br-s2*b*X*Br/(s+N);
          gi*X*(1-X)+ g2*(gX*N-dX*X);
          -d*C];
end

end %end main function/program
