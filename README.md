# A Knowledge Compilation Take on Binary Polynomial Optimization

This repository is a companion to the paper [A Knowledge Compilation Take on Binary Polynomial Optimization](https://arxiv.org/abs/2311.00149), by Florent Capelli, Alberto Del Pia and Silvia Di Gregorio. It contains several scripts illustrating the techniques presented in this paper. 

In this paper, we study the Binary Polynomial Optimization problem: given a multilinear polynomial $p(x_1,\dots,x_n)$, find the point in $(a_1,\dots, a_n) \in \{0,1\}^n$ such that $p(a_1,\dots,a_n)$ is minimal. We solve this problem by first translating it into a weight propositional logic formula and use a modified #SAT solver to solve it. 

## Converting polynomials 

A multilinear polynomial is given in a text file as follows:

- Each non-empty line of the file is monomial
- A monomial $\alpha_e \prod_{i \in e} x_i$ is described with the line $\alpha_e {i_1} \dots {i_k}$ where $e = \{x_{i_1}, \dots, x_{i_k}\}$. 
Lines starting with `c` are ignored. For example, the polynomial $3x_1x_2 - 2 x_1 x_3 + 3 x_1 x_2 x_3$ is represented as the text file:

```
c A representation of 3x_1x_2 - 2 x_1 x_3 + 3 x_1 x_2 x_3
3 1 2
-2 1 3
3 1 2 3
```


Several examples can be found in the directory `examples/poly`. The script `tools/convert.py` takes a file representing a polynomial and convert it into several formats. It prints the output on `stdout`. The precise usage is:

```
python3 convert.py input.poly output-format
```

The possible output formats are:

- `pip` file format. More details on the [POLIP website](https://polip.zib.de/pipformat.php).
- `lp` file format. More details on [CPLEX documentation](https://www.ibm.com/docs/en/icos/22.1.0?topic=cplex-lp-file-format-algebraic-representation). In this case, the problem is casted into a linear program as follows. Each monomial $m = \alpha_m \prod_{i \in I} x_i$ of $p$ is encoded using a fresh binary variable $y_m$ and linear constraints:
  - $y_m \leq x_i$ for every $i \leq m$
  - $\sum_{i \in I} x_i \leq |I|-1+y_m$
And the objective function is to minimize $\sum_{m \in p} y_m$. 
- `wcnf` file format. In this case, the problem is encoded as a weighted CNF formula (in the [DIMACS format](https://jix.github.io/varisat/manual/0.2.0/formats/dimacs.html)) as described in the paper. A monomial is encoded as $y_m \Leftrightarrow \bigwedge_{i \in I} x_i$ and $y_m$ is given a weight of $\alpha_m$; every other literal is given a $0$ weight. An algebraic model counting over the $(min,+)$-semiring then gives the desired value. 

For convenience, we provide the `wcnf`, `lp` and `pip` representation of the Bernasconi instances from [POLIP](https://polip.zib.de/autocorrelated_sequences/) in the `example` directory.

## Using Knowledge Compilation

### Toy examples

Once converted into a weighted CNF formula, the BPO problem can be solved using standard tools from propositional logic theory. The simplest approach is to find the smallest value by using a branching algorithm, where variables are branched on a value one after the others.  Indeed, if $\phi$ is a propositional formula and $x$ a variable of $\phi$, we can find the best assignment $w(\phi)$ as $\max (w(x)+w(\phi|x), w(\neg x)+w(\phi|\neg x))$. 

When a model is found, its weight is reported and we backtrack to the last decision. If done naively, this algorithm boils down to enumerating every model of the formula and is not efficient. We can add many interesting improvement to this naive algorithm:

- Keep a cache of formulas already solved because sometimes, the same formula may appear under distinct partial assignments. For example, for $\phi = (x \vee y \vee z) \wedge (\neg x \vee y \vee z)$, we have that $\phi|x$ and $\phi|\neg x$ are syntactically equivalent to $(y \vee z)$ after removing satisfied clauses and assigned literals. Hence if we have cached the value of $w(\phi|x)$, there is no need to redo the computation for $\phi|\neg x$. 
- Detect, at each step, when the formula is made of more than one connected components, which can be maximized independently. Indeed if $\phi = \phi_1 \wedge \phi_2$ and $var(\phi_1) \cap \var(\phi_2) = \emptyset$, we can see that $w(\phi) = w(\phi_1) + w(\phi_2)$. 
- Use a SAT solver to avoid visiting unsatisfiable branches.

This algorithm known as exhaustive DPLL actually builds a factorized representation of the set of models of the Boolean formula, known as a decision-DNNF circuit (decision Decomposable Normal Form). This representation can in turn be used to find the best assignment and even an extended formulation of the multilinear polytope. Check the paper for details and interesting theoretical results for BPO based on this observation.

We provide a script `tools/compile.py` which implements a very unoptimized version of exhaustive DPLL in Python. It can be used as follows:

```
python3 tools/compile.py input-polynomial.poly
```

This script outputs on `stdout` a json representation of a DNNF computing the multilinear polytope of the input polynomial. This json representation may be used to:

- Export the DNNF to a [graphviz](https://graphviz.org/) file for visualization purpose using `dnnf2dot.py`. The circuit is also annotated with the weight of the minimal model of each gate, showing how the dynamic programming works on DNNF to compute the minimal model. To build a PDF for the figure from the output `dnnf.dot` of `dnnf2dot.py`, use `dot -Tpdf dnnf.dot > dnnf.pdf` (**todo**)
- Compute an extended formulation of the multilinear polytope of size linear in the circuit using `extended.py` (**todo**),

### A modified version of d4

[d4](https://github.com/jm62300/d4) is a knowledge compiler and model counter mainly developped by [Jean-Marie Lagniez](https://www.cril.fr/~lagniez/) from CRIL, Université d'Artois. It implements the procedure highlighted previously in a very efficient way, which allows to scale our method to harder problems. Unfortunately, the current version does not support model counting over arbitrary semirings. We have added it in the [following fork](https://github.com/fcapelli/d4) of `d4` on the `maxplus-demo` branch (which is the default one). 

One can build an executable from this repository which aggregates over the $(\min,+)$-semiring. The relevant part is in the folder `demo/semiring`. After building it with `demo/semiring/build.sh`, one can run  `demo/semiring/build/semiring -i instance.wcnf` to find the minimal satisfying assignment of the weighted CNF formula represented by `instance.wcnf`. This can be used right out-of-the-box with the instances from the `example` folder of this repository. 

While `d4` is able to build a DNNF from the input CNF formula, we have not yet implemented the extraction of the extended formulation from it.
