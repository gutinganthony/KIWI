import random, math
random.seed(3)
T=4000; rho=0.96; k=0.2
e=[0.0]; de=[-0.6]; p=[3.0]
for t in range(1,T):
    e.append(e[-1]+0.02+random.gauss(0,0.05))
    de.append(-0.6+0.8*(de[-1]+0.6)+random.gauss(0,0.05))
    p.append(e[-1]+2.8+0.9*(p[-1]-e[-2]-2.8)+random.gauss(0,0.1))
d=[e[i]+de[i] for i in range(T)]
# define returns by the log-linear approximation (so identity exact up to truncation)
r=[None]+[k+rho*p[t+1]+(1-rho)*d[t+1]-p[t] for t in range(T-1)]
t=0; N=1500
rhs = k/(1-rho)+sum(rho**j*((e[t+1+j]-e[t+j]) - r[t+1+j] + (1-rho)*(d[t+1+j]-e[t+1+j])) for j in range(N))
print("p-e", round(p[t]-e[t],6), "identity", round(rhs,6))
