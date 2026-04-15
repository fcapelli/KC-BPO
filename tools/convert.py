import sys

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

def poly2wcnf(p):
    nclauses = sum([1+len(m[1]) for m in p['poly']])
    print(f"p cnf {p['nvar']+len(p['poly'])} {nclauses}")
    print(f"c Polynomial has {p['nvar']} variables and {len(p['poly'])} monomials")
    print(f"c Original variables from 1 to {p['nvar']}")
    print(f"c Monomials variables from {p['nvar']+1} to {p['nvar']+len(p['poly'])}")
    for i in range(p['nvar']):
        print(f"c p weight {i+1} 0 0")
        print(f"c p weight {-(i+1)} 0 0")
    clauses = []
    for i,m in enumerate(p['poly']):
        midx = 1+i+p['nvar']        
        print(f"c p weight {midx} {m[0]} 0")
        print(f"c p weight {-midx} 0 0")
        print(f"{midx} "+' '.join([f"-{x}" for x in m[1]])+" 0")
        for i in m[1]:
            print(f"-{midx} {i} 0")

def poly2pip(p):
    print("Minimize")
    print("obj: +1 z ")
    print("Subject to")
    print("interacting_sp@0: -1 z")
    for m in p["poly"]:
        sg = "+" if m[0]>=0 else "-"
        print(f"{sg}{abs(m[0])} "+" ".join([f"x#{i}" for i in m[1]]))
    print("<= 0")
    print("Bounds")
    print("z free")
    print("Binary")
    print(" ".join([f"x#{i+1}" for i in range(p["nvar"])]))
    print("End")

def poly2lp(p):
    print("Minimize ")
    print(" obj: +1 z")
    print(" Subject to")
    mon = []
    cst = []
    for i,m in enumerate(p["poly"]):
        sg = "+" if m[0]>0 else "-"
        mon.append(f"{sg}{abs(m[0])} y#{i}")
        for x in m[1]:
            cst.append(f"y#{i} - x#{x} <= 0")
        cst.append(" + ".join([f"x#{j}" for j in m[1]])+f" - y#{i} <= {len(m[1])-1}")
    print("cobj: -1 z "+" ".join(mon)+" <= 0")
    for i,c in enumerate(cst):
        print(f"cst{i}: {c}")
    print("Bounds")
    print("z free")
    print("Binary")
    print(" ".join([f"x#{i+1}" for i in range(p["nvar"])]) + " ".join([f"y#{i}" for i in range(len(p["poly"]))]))
    print("End")

def main():
    outformats = ["pip", "lp", "wcnf"]

    if len(sys.argv)!=3 or sys.argv[2] not in outformats:
        print(f"Usage: {sys.argv[0]} file.poly outputformat")
        print("Allows output format: "+" ".join(outformats))
        exit(0)

    t = sys.argv[2]
    with open(sys.argv[1]) as f:
        lines=f.readlines()
        f.close()

    p = parse_poly(lines)
    print(p, file=sys.stderr)
    if t == "pip":
        poly2pip(p)
    elif t == "lp": 
        poly2lp(p)
    elif t == "wcnf":
        poly2wcnf(p)
    exit(1)
    

if __name__ == "__main__":
    main()
