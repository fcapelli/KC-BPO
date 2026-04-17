#!/usr/bin/python3
import sys
import json

def parse_poly(lines):
    r = []
    n = 0
    for s in lines:
        if s[0] != "c": 
            m = s.split(" ")
            mon = [int(x) for x in m[1:]]
            n = max(n, max(mon))
            r.append((int(m[0]), mon))
    return {"poly": r, "nvar": n}

def poly2cnf(p):
    names= {}
    weights = {}
    n = p["nvar"] #max([max(m) for m in p])
    for i in range(n):
        names[i+1] = f"x_{{{i+1}}}"
        weights[f"x_{{{i+1}}}"] = (0,0)
    lm = 1
    cnf = []
    for m in p["poly"]:
        y = n+lm
        ny = f"y_{{{','.join(map(str,m[1]))}}}"
        names[y] = ny
        weights[ny] = (0,m[0])
        rp = [-i for i in m[1]]
        rp.append(y)
        cnf.append(frozenset(rp))
        for i in m[1]:
            cnf.append(frozenset([-y, i]))
        lm += 1
    return (frozenset(cnf), names, weights)

def set_literal(f,l):
    nf = set({})
    for c in f:
        if -l in c:
            nf.add(c.difference({-l}))
        elif l not in c:
            nf.add(c)
    return frozenset(nf)
        
def find(x,d):
    if x not in d:
        d[x]=x
        return x
    else:
        root = x
        while d[root] != root:
            root = d[root]
        while d[x] != root:
            p = d[x]
            d[x] = root
            x = p
        return root
    
def union(x,y,d):
    x = find(x,d)
    y = find(y,d)
    if x != y:
        d[y] = x
        
def cc(f):
    d = {}
    for c in f:
        x0=None
        for l in c:
            x = abs(l)
            if x0 is None:
                x0=x
            union(x0,x,d)
    for x in d:
        find(x,d)
    cc = {}
    for c in f:
        x = find(abs(next(iter(c))), d)
        if x in cc:
            cc[x] = cc[x].union(frozenset([c]))
        else:
            cc[x] = frozenset([c])
    return cc
    

def dpll(f,names, tau, r, pi=None):
    def sgn(l,v0,v1):
        return (v0 if l < 0 else v1)

    def vars(f):
        v=set()
        for c in f:
            for l in c:
                v.add(abs(l))
        return v
    
    def firstvar(f):
        v = None
        for c in f:
            for l in c:
                if v is None or (pi is None and abs(l) < v) or (pi is not None and pi[abs(l)] < pi[v]):
                    v = abs(l)
        return v
            
    # intialize memory
    if "nodes" not in r:
        r["nodes"] = [{"type": "bot"},  {"type": "top"}]
    if "cache" not in r:
        r["cache"] = {}
    if "id" not in r:
        r["id"]=1


    # No clause left   
    if len(f) == 0:
        return 1

    # Inconsistent clause
    if frozenset() in f:
        return 0

    # Cache lookup
    if f in r["cache"]:
        return r["cache"][f]

    # Otherwise, create a new node
    r["id"] += 1
    id1 = r["id"]
    r["nodes"].append({})
    
    # Add r to the cache
    r["cache"][f] = id1

    # Connected components
    comp = cc(f)
    b = True
    if len(comp) > 1:
        inputs = []
        for g in comp:
            v = dpll(comp[g],names,tau,r)
            inputs.append(v)
        r["nodes"][id1] = {"type": "and", "inputs": inputs}
        return id1

    vl = []
    for c in f: # looks for unit propagation (UP)
        if len(c) == 1:
            l = next(iter(c))
            vl.append(l)
            break
        
    if not(vl): # UP not found, we pick the first variable and try both literals
        l = firstvar(f)
        vl = [l, -l]

    inputs = [None, None]
    for l in vl:
        tau.append(l)        
        f1 = set_literal(f,l)
        v = dpll(f1,names,tau,r)
        inputs[sgn(l,0,1)] = v
        tau.pop()

    r["nodes"][id1] = {"type" : "dec", "var" : names[abs(vl[0])], "inputs": inputs}

    return id1
        
    
def main():
    if len(sys.argv)<=1:
        print(f"Usage: {sys.argv[0]} polynomial.poly")
        exit(1)

    with open(sys.argv[1]) as f:
        p = parse_poly(f.readlines())
        f.close()
    cnf,names,weights = poly2cnf(p)
    r={}
    root = dpll(cnf,names,[],r)
    print(json.dumps({"root" : root, "nodes": r["nodes"], "weights": weights,  "poly": p["poly"]}, indent=3))

        

if __name__ == '__main__':
    main()
    

