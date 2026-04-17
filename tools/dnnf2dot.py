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
        newcircuit["nodes"][idn] = nodes[idn]
        cache[idn] = idn
        newcircuit["nodes"][idn]["inputs"] = [normalizeDNNF_aux(nodes, i, cache, newcircuit) for i in nodes[idn]["inputs"]]
        
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
        
    if node["type"] in ["and", "or"]:
        for i in node["inputs"]:
            annotate_dnnf(dnnf, i, stamp)
            dnnf["nodes"][i]["outputs"].add(n)
            node["vars"].update(dnnf["nodes"][i]["vars"])
        return
    
    if node["type"] == "dec":
        for i in node["inputs"]:
            node["vars"].add(node["var"])
            
            if i is not None:
                annotate_dnnf(dnnf, i, stamp)
                dnnf["nodes"][i]["outputs"].add(n)
                node["vars"].update(dnnf["nodes"][i]["vars"])
        return
        

    if node["type"] in ["bot", "top"]:
        return

    if node["type"]=="input":
        node["vars"].add(node["var"])
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
                                        val: b,
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
    return orcst+andcst+incst
        
def main():
    f = sys.stdin
    if len(sys.argv) <= 1:
        print("Reading standard input", file=sys.stderr)
    else:
        f = open(fname)
    d = normalizeDNNF(json.load(f))
    f.close()
    
    # compute variables and outputs
    stamp = 0
    annotate_dnnf(d,d["root"],stamp)    
    stamp+=1
    
    # clean unused variables
    useless = []
    for k in d["nodes"]:
        if "stamp" not in d["nodes"][k]:
            useless.append(k)
    for k in useless:
        d["nodes"].pop(k)

    # smooth
    smooth_dnnf(d)
    annotate_dnnf(d,d["root"],stamp+1) # not necessary
    
    print(d, file=sys.stderr)
    print("\n".join(extended_formulation(d)), file=sys.stderr)
    dnnf2dot(d)
    
if __name__ == '__main__':
    main()
    


