import sys
import json
# clause = frozen set of numbers, 1 = x_1, -1 = \neg x_1
# cnf = frozen set of clauses

def poly2cnf(p):
    n = max([max(m) for m in p])
    lm = 1
    cnf = []
    for m in p:
        y = n+lm
        rp = [-i for i in m]
        rp.append(y)
        cnf.append(frozenset(rp))
        for i in m:
            cnf.append(frozenset([-y, i]))
        lm += 1
    return frozenset(cnf)

def ass_str(tau):
    return ",".join([f"x{k}" if k>0 else f"~x{-k}" for k in sorted(tau, key=abs)])

def ass_id(tau):
    return "N"+"".join([f"x{k}" if k>0 else f"nx{-k}" for k in sorted(tau, key=abs)])

def ass_tex(tau):    
    return "$\\langle "+",".join([f"x_{k} \\mapsto 1" if k>0 else f"x_{-k} \\mapsto 0" for k in sorted(tau, key=abs)])+" \\rangle$"

def set_literal(f,l):
    nf = set({})
    for c in f:
        if -l in c:
            nf.add(c.difference({-l}))
        elif l not in c:
            nf.add(c)
    return frozenset(nf)
        
def cnf_str(f):
    return "$("+") \\wedge (".join([" \\vee ".join([f"x_{k}" if k>0 else f"\\neg x_{-k}" for k in sorted(list(c), key=abs)]) for c in f])+")$"

def cnf_id(f):
    flist = sorted(list([sorted(list(c)) for c in f]))
    return "A".join(["v".join([f"x{k}" if k>0 else f"nx{-k}" for k in c]) for c in flist])

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
    

def dpll(f, tau, opt, r, pi=None):
    def sgn(l,v0,v1):
        return (v0 if l < 0 else v1)
    def firstvar(f):
        v = None
        for c in f:
            for l in c:
                if v is None or (pi is None and abs(l) < v) or (pi is not None and pi[abs(l)] < pi[v]):
                    v = abs(l)
        return v
    
    def insert_dot(s):
        r["dot"][r["fragment"]] = s
        r["call"][r["fragment"]] = (f,tau.copy())
        r["fragment"] += 1
    def node_name(f,tau):
        return(f"{ass_id(tau)}{cnf_id(f)}")
        
    # intialize memory and options
    if "cache" not in opt:
        opt["cache"] = False
    if "dnnf" not in opt:
        opt["dnnf"] = False        
    if "dot" not in r:
        r["dot"] = {}        
    if "inputs" not in r:
        r["inputs"] = set()        
    if "fragment" not in r:
        r["fragment"] = 0        
    if "call" not in r:
        r["call"] = {}
    if "cache" not in r:
        r["cache"] = {}
        insert_dot(f"top [label=1]")
        insert_dot(f"bot [label=0]")
    if "names" not in r:
        r["names"] = {}
    if "id" not in r:
        r["id"]=0

    r["id"] += 1
    id1 = r["id"]
    if f in r["cache"]:
        id1 = r["cache"][f]
        return r["names"][id1] # cache hit, return names

    # Generic names
    r["cache"][f] = id1 
    r["names"][id1] = f"N{id1}"

    # One clause left of size one
    if len(f) == 1:
        c = next(iter(f))
        if len(c) == 1:
            l=next(iter(c))
            # insert new literal name
            name = f"I{abs(l)}v{sgn(l,0,1)}"
            if l not in r["inputs"]:                
                insert_dot(f"{name} [label={sgn(l,'¬','')}x{abs(l)}]")
                r["inputs"].add(l)
            r["names"][id1] = name
            return name


    # No clause left   
    if len(f) == 0:
        return "top"
    
    if frozenset() in f:
        insert_dot(f"{r['names'][id1]} [label=0]")
        return "bot"
     

    if "cc" in opt and opt["cc"]:
        comp = cc(f)
        b = True
        if len(comp) > 1:
            insert_dot(f"{r['names'][id1]} [label=∧]")
            for g in comp:
                v = dpll(comp[g], tau, opt, r)
                if opt["dnnf"]:
                    insert_dot(f"{v} -> {r['names'][id1]}")
                else:
                    insert_dot(f"{r['names'][id1]} -> {v} [style={sgn(l,'dashed', 'solid')}]")
            return r['names'][id1]

    vl = []
        
    for c in f: #look for unit propagation
        if len(c) == 1:
            l = next(iter(c))
            vl.append(l)
            insert_dot(f"{r['names'][id1]} [label=∧]")
            if opt["dnnf"]:
                if l not in r["inputs"]:
                    insert_dot(f"I{abs(l)}v{sgn(l,0,1)} [label={'¬' if l < 0 else ''}x{abs(l)}]")
                    r["inputs"].add(l)
                insert_dot(f"I{abs(l)}v{sgn(l,0,1)} -> {r['names'][id1]}")
            else:
                insert_dot(f"{r['names'][id1]} [label=x{abs(l)}]")

        break
        
    if not(vl): # up not found
        l = firstvar(f)
        vl = [l, -l]

        if opt["dnnf"]:
            insert_dot(f"{r['names'][id1]} [label=∨]")
            insert_dot(f"{r['names'][id1]}a0 [label=∧]")
            insert_dot(f"{r['names'][id1]}a1 [label=∧]")
            
            # add input only once
            if -abs(l) not in r["inputs"]:
                insert_dot(f"I{abs(l)}v0 [label=¬x{abs(l)}]")
                r["inputs"].add(-abs(l))

            if abs(l) not in r["inputs"]:                
                insert_dot(f"I{abs(l)}v1 [label=x{abs(l)}]")
                r["inputs"].add(abs(l))
                
            insert_dot(f"I{abs(l)}v0 -> {r['names'][id1]}a0 -> {r['names'][id1]}")
            insert_dot(f"I{abs(l)}v1 -> {r['names'][id1]}a1 -> {r['names'][id1]}")
        else:
            insert_dot(f"{r['names'][id1]} [label=x{abs(l)}]")


    for l in vl:
        tau.append(l)        
        f1 = set_literal(f,l)
        v = dpll(f1,tau,opt,r)
        suffix = "" if len(vl)<2 else f"a{sgn(l,0,1)}"
        if opt["dnnf"]:
            insert_dot(f"{v} -> {r['names'][id1]}{suffix}")
        else:
            insert_dot(f"{r['names'][id1]} -> {v} [style={sgn(l,'dashed','solid')}]")
        tau.pop()

    return r['names'][id1]
    

def strTrace(r, anim=True,prefix=""):
    out = {}
    out["graph"] = "digraph {\nbgcolor=none\nrankdir=BT\n"
    out["cnf"] = '<div class="rstack">'

    
    for k in r["dot"]:
        fidx = f"{prefix}{k}"
        l = r["dot"][k]
        if anim:
            l = f"{l[:-1]}, class=fragment, dataFragment={fidx}]"        
        out["graph"]+=l+"\n"
    out["graph"] += "\n}"

    keys = sorted(r["call"].keys())
    
    for k in keys:
        fidx = f"{prefix}{k}"
            
        (f,tau) = r["call"][k]

        attr=""
        if anim:
            attr = f'class="fragment fade" data-fragment-index="{fidx}"'
        l = f'<div {attr}><div class="cnf">{cnf_str(f)}</div><div class="assignment">{ass_tex(tau)}</div></div>'
        out["cnf"] += l+"\n"
    out["cnf"] += "\n</div>"
    return out
    
    

def print_slide(f, opt={"up":True, "exhaustive":True, "fragment": 1}):
    r={}
    dpll(f,[],opt, r)
    o = strTrace(r)

    print(":::row")
    print('```{.pandoc-compile data-language="dot"}')
    print(o["graph"])
    print('```')
    print(o["cnf"])
    print(":::")

    
def main():
    f1 = frozenset([
        frozenset([1,3,-4]),
        frozenset([1,-2,-3,4]),
        frozenset([-1,2,4]),
        frozenset([1,4]),
        # frozenset([-1,-2]),
        # frozenset([-1,2,-4])
    ]
                   )

    f2 = frozenset([
        frozenset([1,2,3]),
        frozenset([-1,2,3]),
        frozenset([1,-4]),
        frozenset([-1,-4]),
    ])

    if len(sys.argv)<=1:
        # −3x1 x2 x3 + 4x4 x5 + 5x2 x3 x4 x5 x6
        f = poly2cnf([[1,2,3],[4,5], [2,3,4,5,6]])
        opt = {"up":True, "exhaustive":True, "fragment": 1, "cache": True, "cc": True, "dnnf": True}
        r={}
        dpll(f,[],opt, r)
        o = strTrace(r, anim=False)
        print(o["graph"])
        print(r, file=sys.stderr)
        exit(0)
        

    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            opt = json.load(f)
    else:
        opt = {"up":True, "exhaustive":True, "fragment": 1}
        
    with open(sys.argv[1]) as f:
        cnf = frozenset([frozenset([int(x) for x in l.split()]) for l in f.readlines()])
        print_slide(cnf, opt)
        #print(cc(cnf))
        # print(cnf_id(cnf))

if __name__ == '__main__':
    main()
    

