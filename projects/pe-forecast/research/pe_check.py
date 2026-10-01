import math
r, ROE, b = 0.09, 0.15, 0.4
g = b*ROE
E1 = 1.0
# brute-force DDM forward P/E
P = sum((1-b)*E1*(1+g)**(t-1)/(1+r)**t for t in range(1,5000))
gordon = (1-b)/(r-g)
mm = 1/r + b*(ROE-r)/(r*(r-g))
lk = 1/r + (1/r-1/ROE)*(g/(r-g))
print("DDM brute", round(P,6), "Gordon", round(gordon,6), "MM/PVGO", round(mm,6), "L&K", round(lk,6))
# ROE = r -> P/E = 1/r for any b
for bb in (0,0.3,0.8):
    gg=bb*r; print("ROE=r b=",bb, round((1-bb)/(r-gg),6), "1/r=",round(1/r,6))
# Two-stage Damodaran forward vs brute force (trailing P0/E0)
gh, n, ph, gn, pn = 0.25, 5, 0.2, 0.08, 0.5
r2 = 0.12
E0 = 1.0
brute = 0.0
E = E0
for t in range(1, 6000):
    if t <= n:
        E *= (1+gh); d = ph*E
    else:
        E *= (1+gn); d = pn*E
    brute += d/(1+r2)**t
formula = ph*(1+gh)*(1-((1+gh)**n)/((1+r2)**n))/(r2-gh) + pn*((1+gh)**n)*(1+gn)/((r2-gn)*(1+r2)**n)
print("two-stage brute", round(brute,6), "formula", round(formula,6))
# OJ: P0 = eps1/r + z1/(r(r-(gam-1)))  vs brute AEG sum
r3, eps1, eps2, dps1, gl = 0.08, 1.0, 1.15, 0.3, 0.03
z1 = eps2 + r3*dps1 - (1+r3)*eps1
brute = eps1/r3 + sum(z1*(1+gl)**(t-1)/(1+r3)**t for t in range(1,8000))/r3
g2 = (eps2-eps1)/eps1
oj = eps1*(g2 - gl + r3*dps1/eps1)/(r3*(r3-gl))
A = 0.5*(gl + dps1/oj)
rimp = A + math.sqrt(A*A + (eps1/oj)*(g2-gl))
print("OJ brute", round(brute,6), "OJ closed", round(oj,6), "GM implied r", round(rimp,6))
# Penman trailing identity check with RIV, random path
import random
random.seed(1)
rho = 1.1; B_prev = 10.0
X = [None]; B=[B_prev]; d=[None]
for t in range(1,3000):
    x = 0.12*B[-1]*(1+0.5*math.exp(-t/5)) if t<2000 else 0
    dv = 0.5*x
    X.append(x); d.append(dv); B.append(B[-1]+x-dv)
Xa = [None]+[X[t]-(rho-1)*B[t-1] for t in range(1,len(X))]
t0 = 1
V = B[t0] + sum(Xa[t0+k]/rho**k for k in range(1,1900))
lhs = (V + d[t0])/X[t0]
rhs = rho/(rho-1)*(1 + sum((Xa[t0+k]-Xa[t0+k-1])/rho**k for k in range(1,1900))/X[t0])
print("Penman trailing identity lhs", round(lhs,6), "rhs", round(rhs,6))
# Ohlson weights check (nu=0)
R, w = 1.1, 0.6
y_prev, x, dd = 10.0, 1.5, 0.6
y = y_prev + x - dd
xa = x - (R-1)*y_prev
P1 = y + w/(R-w)*xa
k = (R-1)*w/(R-w); phi = R/(R-1)
P2 = k*(phi*x - dd) + (1-k)*y
print("Ohlson direct", round(P1,6), "weighted avg", round(P2,6))
# Campbell-Shiller P/E identity check (exact path, log-linear)
