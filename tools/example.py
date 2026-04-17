#!/usr/bin/python3
import sys
import json

# normalize a decision DNNF into a proper DNNF
def normalizeDNNF(dnnf):
    newcircuit = {"nodes": {}, "inputs": {}, "id": len(dnnf["nodes"])}
    r = normalizeDNNF_aux(dnnf["nodes"], dnnf["root"], {}, newcircuit)
    return {"root" : r, "weights": dnnf["weights"], "nodes": newcircuit["nodes"]}

def normalizeDNNF_aux(nodes, idn, cache, newcircuit): 
    if idn in cache:
        return cache[idn]
    
    cache[idn] = "ERR" # temporary value
    
    if nodes[idn]["type"] == "and" or nodes[idn]["type"] == "or":
        newcircuit["nodes"][idn] = {"type": nodes[idn]["type"], "inputs": []}
        cache[idn] = idn

        for i in nodes[idn]["inputs"]:
            j = normalizeDNNF_aux(nodes, i, cache, newcircuit)
            if newcircuit["nodes"][j]["type"] == nodes[idn]["type"]:
                newcircuit["nodes"][idn]["inputs"] += newcircuit["nodes"][j]["inputs"]
            else:
                newcircuit["nodes"][idn]["inputs"].append(j)
#        newcircuit["nodes"][idn]["inputs"] = [ for i in nodes[idn]["inputs"]]
        
    elif nodes[idn]["type"] == "dec": 
        v = nodes[idn]["var"]
        nodeinputs = nodes[idn]["inputs"]
        activeinputs = [(i,j) for (i,j) in enumerate(nodeinputs) if j is not None]

        newcircuit["nodes"][idn] = {"type" : "or", "inputs" : []}
        for (i, id2) in activeinputs:
            if (v,i) not in newcircuit["inputs"]: # print input if node done yet
                id1 = newcircuit["id"]
                newcircuit["id"]+=1
                newcircuit["inputs"][(v,i)] = id1
                newcircuit["nodes"][id1] = {"type" : "input", "var" : v, "val" : i}                
                
            if len(activeinputs) > 1: # no unit propagation
                ida = newcircuit["id"]
                newcircuit["id"] += 1
                newcircuit["nodes"][idn]["inputs"].append(ida)
                newcircuit["nodes"][ida] = {"type": "and",
                                            "inputs": [newcircuit["inputs"][(v,i)], normalizeDNNF_aux(nodes, id2, cache, newcircuit) ]
                                            }
                cache[idn] = idn
                
            else: # there is a unit propagation
                if nodes[id2]["type"] != "top":
                    newcircuit["nodes"][idn]["type"]="and"
                    newcircuit["nodes"][idn]["inputs"].append(newcircuit["inputs"][(v,i)])
                    newcircuit["nodes"][idn]["inputs"].append(normalizeDNNF_aux(nodes, id2, cache, newcircuit))
                    cache[idn] = idn
                else:
                    cache[idn] = newcircuit["inputs"][(v,i)]
    elif nodes[idn]["type"] == "input":
        newcircuit["nodes"][idn] = nodes[idn].copy()
        cache[idn]=idn
        
    return cache[idn]

def dnnf2tikz(dnnf):
    print("\\resizebox{\\columnwidth}{!}{")
    print("\\begin{tikzpicture}[>=stealth]\n \
    \\graph [layered layout, grow=up, level distance=1in,\n \
    sibling distance=0.5in, edge quotes={fill=background, inner sep=1.25pt, font=\\ttfamily\\scriptsize}]\n \
    {")
    dnnf2tikz_aux(dnnf["nodes"], dnnf["root"], {}, {})
    print("};\n \
    \\end{tikzpicture}}")

def dnnf2tikz_aux(nodes, idn, cache, inputs):
    if idn in cache:
        return cache[idn]
    cache[idn] = "ERR"
    w = f"\\textbf{{\\color{{red}} {nodes[idn]['min']}}}"
    idnstr = f"\\textbf{{\\color{{blue}} {idn}}}"
    if nodes[idn]["type"] == "and":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [as={{\\small: {idnstr}|{w}}},wedge];")
        for i in nodes[idn]["inputs"]:
            ni = dnnf2tikz_aux(nodes, i, cache, inputs)
            print(f"{ni} -> N{idn};")
            
    elif nodes[idn]["type"] == "or":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [as={{\\small: {idnstr}|{w}}},vee];")
        for i in nodes[idn]["inputs"]:            
            print(f"{dnnf2tikz_aux(nodes, i, cache, inputs)} -> N{idn};")
            
        
    elif nodes[idn]["type"] == "dec":
        cache[idn] = f"N{idn}"

        v = nodes[idn]["var"]
        nodeinputs = nodes[idn]["inputs"]
        
        print(f"N{idn} [as={v},decision];")
        for (i, id2) in enumerate(nodeinputs):
            if id2 is not None:
                print(f"{dnnf2tikz_aux(nodes, id2, cache, inputs)} ->[{'dashed' if i==0 else ''}] N{idn};")

    elif nodes[idn]["type"] == "input":
        cache[idn] = f"N{idn}"
        neg = "\\neg "
        print(f"N{idn} [as={neg if nodes[idn]['val']==0 else ''}{nodes[idn]['var']}: {{{idnstr}| {w}}}, input];")
                
    elif nodes[idn]["type"] == "bot":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [as={{\\small: {idnstr}|{w}}},bot];")

    elif nodes[idn]["type"] == "top":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [as={{\\small: {idnstr}|{w}}},top];")

    else:
        raise Exception("Unknown type")
    return cache[idn]


def dnnf2dot(dnnf):
    print("digraph g {")
    print("rankdir=BT")
    dnnf2dot_aux(dnnf["nodes"], dnnf["root"], {}, {})
    print("}")
    
def dnnf2dot_aux(nodes, idn, cache, inputs):
    if idn in cache:
        return cache[idn]
    cache[idn] = "ERR"
    if nodes[idn]["type"] == "and":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [label=∧]")
        for i in nodes[idn]["inputs"]:            
            print(f"{dnnf2dot_aux(nodes, i, cache, inputs)} -> N{idn}")
            
    elif nodes[idn]["type"] == "or":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [label=∨]")
        for i in nodes[idn]["inputs"]:            
            print(f"{dnnf2dot_aux(nodes, i, cache, inputs)} -> N{idn}")
            
        
    elif nodes[idn]["type"] == "dec":
        cache[idn] = f"N{idn}"

        v = nodes[idn]["var"]
        nodeinputs = nodes[idn]["inputs"]
        
        print(f"N{idn} [label=\"{v}\"]")
        for (i, id2) in enumerate(nodeinputs):
            if id2 is not None:
                print(f"{dnnf2dot_aux(nodes, id2, cache, inputs)} -> N{idn} [style={'dashed' if i==0 else 'solid'}]")

    elif nodes[idn]["type"] == "input":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [label=\"{'¬' if nodes[idn]['val']==0 else ''}{nodes[idn]['var']}\"]")
                
    elif nodes[idn]["type"] == "bot":
        print("this is a bot")
        cache[idn] = f"N{idn}"
        print(f"N{idn} [label=0]")

    elif nodes[idn]["type"] == "top":
        cache[idn] = f"N{idn}"
        print(f"N{idn} [label=1]")

    else:
        raise Exception("Unknown type")
    return cache[idn]

def annotate_dnnf(dnnf, n, stamp):
    node = dnnf["nodes"][n]
    if "stamp" in node and node["stamp"] == stamp:
        return

    node["stamp"] = stamp
    if "vars" not in node:
        node["vars"] = set()
    if "outputs" not in node:
        node["outputs"] = set()
    if "min" not in node:
        node["min"] = None
        
    if node["type"]=="and":
        m = 0
        for i in node["inputs"]:
            annotate_dnnf(dnnf, i, stamp)
            dnnf["nodes"][i]["outputs"].add(n)
            node["vars"].update(dnnf["nodes"][i]["vars"])            
            m += dnnf["nodes"][i]["min"]
        node["min"] = m
        return
    
    if node["type"]=="or":
        m = None
        for i in node["inputs"]:
            annotate_dnnf(dnnf, i, stamp)
            dnnf["nodes"][i]["outputs"].add(n)
            node["vars"].update(dnnf["nodes"][i]["vars"])
            if m is None or dnnf["nodes"][i]["min"] < m:
                m = dnnf["nodes"][i]["min"]
        node["min"] = m
        return

    if node["type"] == "dec":
        for i in node["inputs"]:
            node["vars"].add(node["var"])
            w = dnnf["weights"][node["var"]]
            m = None
            if i is not None:                
                annotate_dnnf(dnnf, i, stamp)
                dnnf["nodes"][i]["outputs"].add(n)
                node["vars"].update(dnnf["nodes"][i]["vars"])
                w = dnnf["weights"][node["var"]][node["val"]]
                if m is None or dnnf["nodes"][i]["min"]+w<m:
                    m = dnnf["nodes"][i]["min"]+w<m
            node["min"] = m
        return
        

    if node["type"]=="top":
        node["min"] = 0
        return
    if node["type"]=="bot":
        node["min"] = None
        return

    if node["type"]=="input":
        node["vars"].add(node["var"])
        node["min"] = dnnf["weights"][node["var"]][node["val"]]
        # keep a pointer toward inputs
        if "inputs" not in dnnf:
            dnnf["inputs"] = {}            
        dnnf["inputs"][(node["var"], node["val"])] = n
        return


def smooth_dnnf(d):  # smooth a dnnf ; it must be annotated
    idx = max(d["nodes"].keys())+1
    keys = list(d["nodes"].keys())
    for k in keys:
        current = d["nodes"][k]
        if current["type"] == "or":
            for i in range(len(current["inputs"])):
                child = d["nodes"][current["inputs"][i]]
                
                if current["vars"] != child["vars"]: # not smooth
                    newand = idx
                    idx += 1
                    d["nodes"][newand] = {
                        "type": "and",
                        "inputs": [ current["inputs"][i] ],
                        "outputs" : set([k]),
                        "vars" : current["vars"],
                        "stamp": current["stamp"]
                    }
                    
                    current["inputs"][i] = newand
                    
                    child["outputs"].remove(k)
                    child["outputs"].add(newand)
                    
                    for x in current["vars"]-child["vars"]:

                        if (x,-1) not in d["inputs"]: # we do not have a tautology on x already
                            newor = idx
                            idx += 1
                            d["inputs"][(x,-1)] = newor 
                            d["nodes"][newor] = {
                                "type": "or",
                                "outputs" : set([newand]),
                                "vars" : set([x]),
                                "stamp": current["stamp"],
                                "inputs": []
                            }
                            for b in range(2):
                                if (x,b) not in d["inputs"]:
                                    d["inputs"][(x,b)] = {
                                        "type": "input",
                                        "var" : x,
                                        "vars": set(x),
                                        "val": b,
                                        "outputs" : set([newor]),
                                        "stamp": current["stamp"],
                                    }
                                else:
                                    idinput=d["inputs"][(x,b)]
                                    d["nodes"][idinput]["outputs"].add(newor)
                                d["nodes"][newor]["inputs"].append(d["inputs"][(x,b)])
                                
                        d["nodes"][newand]["inputs"].append(d["inputs"][(x,-1)])

                        
def extended_formulation(dnnf):
    orcst = []
    andcst = []
    incst = []
    def linsum(l, n, out):
        if l:            
            return "+".join([f"z_{{{n,m}}}" for m in l]) if out else "+".join([f"z_{{{m,n}}}" for m in l]) 
        else:
            return "1"
        
    for n in dnnf["nodes"]:
        node = dnnf["nodes"][n]
        if node["type"] == "or":
            orcst.append(f"{linsum(node['inputs'], n, False)} = {linsum(node['outputs'], n, True)}")
        elif node["type"] == "and":
            for e in node["inputs"]:
                andcst.append(f"z_{{{e,n}}} = {linsum(node['outputs'], n, True)}")
        elif node["type"] == "input":
            if node["val"] == 1:
                incst.append(f"{linsum(node['outputs'], n, True)} = 1")
    return (orcst,andcst,incst)
        
def main():
    f = sys.stdin
    if len(sys.argv) <= 1:
        print("Reading standard input", file=sys.stderr)
    else:
        f = open(fname)
    d = json.load(f)
    poly = d["poly"]
    d = normalizeDNNF(d)
    f.close()

    # compute variables and outputs
    stamp = 0
    annotate_dnnf(d,d["root"],stamp)    
    stamp+=1
    
    # smooth
    smooth_dnnf(d)

    # compress gates
    d = normalizeDNNF(d)
    annotate_dnnf(d,d["root"],stamp+1)
    # clean unused variables
    useless = []
    for k in d["nodes"]:
        if "stamp" not in d["nodes"][k]:
            useless.append(k)
    for k in useless:
        d["nodes"].pop(k)

    # Generate example
    
    with open("header.tex") as head:
        print(head.read())
        head.close()
        
    def pretty(p):
        l = []
        for m in p:
            l.append(f"{m[0]}{''.join([f'x_{i}' for i in m[1]])}")
        return "\\[ p = "+'+'.join(l)+".\\]"

    def formula(p):
        l = []
        for m in p:
            w = '\\wedge '
            l.append(f"\\left(y_{{{','.join(map(str,m[1]))}}} \\Leftrightarrow ({w.join([f'x_{i}' for i in m[1]])})\\right)")
        return "\\[ F = "+w.join(l)+".\\]"

    def cnf(p):
        l = []
        for m in p:
            w = '\\wedge \\\\'
            v = '\\vee '
            neg='\\neg '
            y=f"y_{{{','.join(map(str,m[1]))}}}"
            l.append(f"\\left({y} \\vee {v.join([f'{neg}x_{i}' for i in m[1]])}\\right)")
            for x in m[1]:
                l.append(f'(x_{x} {v} {neg}{y})')
        return "\\begin{align*} F = "+w.join(l)+".\\end{align*}"

    print(f"In this example, we consider the polynomial {pretty(poly)}")
    print(f"Its multilinear set can be seen as the sets of satisfying assignments of the following Boolean formula: {formula(poly)}")
    print(f"Encoded as the following CNF formula: {cnf(poly)}")
    print(f"In the next sections, we give a smooth DNNF representing this Boolean function. In addition to their type ($\\vee$, $\\wedge$ or inputs), each gate is annotated with two colored values. The value in blue is an identifier for each node. The value in red is the smallest weight of a satisfying assignment of the gate. The optimal value for the input polynomial is hence the red value in the output node of the circuit. This values are computed bottom up: values for the inputs of the circuits are the weight of the corresponding literal. The value of a $\\vee$-gate is the minimal value of its input. The value of a $\\wedge$-gate is the sum of each value below. \n")
    print("An extended formulation, extracted from the DNNF, is given in the last section. Variable $z_{{i,j}}$ denotes the variables associated to the edge from node having identifier $i$ to node having identifier $j$.")

    print("\\section{A smooth DNNF}")
    dnnf2tikz(d)
    print("\\newpage \\section{The extended formulation} \\begin{multicols*}{2} \\noindent")
    orcst, andcst, incst = extended_formulation(d)
    print("\\subsection{Constraints for $\\vee$-nodes}")
    print("\\\\ \n".join([f"${c}$" for c in orcst]))
    print("\\subsection{Constraints for $\\wedge$-nodes}")
    print("\\\\ \n".join([f"${c}$" for c in andcst]))
    print("\\subsection{Constraints for inputs}")
    print("\\\\ \n".join([f"${c}$" for c in incst]))
    print("\\end{multicols*}")
    with open("tail.tex") as tail:
        print(tail.read())
        tail.close()


    # dnnf2tikz(d)
    
if __name__ == '__main__':
    main()
    


