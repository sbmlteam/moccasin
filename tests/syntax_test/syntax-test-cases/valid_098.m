A2 = accumarray(subs,val,[],@(x) var(x,1))
A = accumarray(subs,val,[],@(x) sum(x,'native'))
A = accumarray(subs,val,[],@(x) {x})
