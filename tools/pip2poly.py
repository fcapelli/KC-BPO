import sys

if len(sys.argv)!=2:
    print(f"Usage: {sys.argv[0]} file.pip")
    exit(0)

err=sys.stderr

f=open(sys.argv[1])
s=f.read()
f.close()

start_contraints = s.find("Subject to")
start_polynomial = s.find(":", start_contraints)
end_polynomial = s.find("<=", start_polynomial)

polynomial = s[start_polynomial+1: end_polynomial]


monomials = []
mon = []
coeff= 0

i=0
while(i < len(polynomial)):
    if polynomial[i] in ["+","-"]:
        if mon:
            monomials.append((coeff, mon))
        mon=[]
        ns=polynomial.find(' ', i)
        coeff=int(polynomial[i:ns])
        i=ns+1
    elif polynomial[i].isspace():
        i+=1
    else:
        ns=polynomial.find(' ', i)
        mon.append(polynomial[i:ns])
        i=ns+1

if mon:
    monomials.append((coeff, mon))

fn=sys.argv[1].split("/")[-1]
print(f"c Source: {fn} \nc from https://polip.zib.de/autocorrelated_sequences/")
lines = [f'{m[0]} '+' '.join([m2.replace("x#","") for m2 in m[1]]) for m in monomials if m[1] != ["z"]]
print('\n'.join(lines))

