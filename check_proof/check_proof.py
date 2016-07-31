import random, json, os
import snappy
import word_problem
import networkx as nx


sample1 = """{"rels":["abbcb","ccAcAB","aabcc"],"group_args":[1,1,0],
"proof":[["a.b","b.a.b.a.b.b.a.a.a.b"],["a.B.c","a.B.c.a.a.c.c"],
["a.B.C","C.a.C.a.a.B"]],"name":"m003(-3,1)","gens":"a.b.c"}"""

sample1 = """{"rels":["abbcb","ccAcAB","aabcc"],"group_args":[1,1,0],
"proof":[["a.b","b.a.b.a.b.b.a.a.a.b"],["a.B.c","a.B.c.a.a.c.c"],
["a.B.C","C.a.C.a.a.B"]],"name":"m003(-3,1)","gens":"a.b.c"}"""

sample2 = """ {"rels":["aacbc","bcBcbA","abcccbabccbabccb"],"group_args":[1,1,0],"proof":[["a.b.c","b.c.a.a.c"],["a.b.C.aB","a.aB.a.a.b.C.a.aB.aB.C.b.aB.a.a.b"],["a.b.C.bA.ca","ca.ca.a.b.a.a"],["a.b.C.bA.AC.Ab.cb.ac","cb.cb.a.ac.ac.a.a.a.a"],["a.b.C.bA.AC.Ab.cb.CA.bc","bc.cb.a.bc.cb.a.bc.cb.cb.a.bc.cb.a.bc.cb.a.a.a.bc.cb.a.bc.cb.a.a.a.bc.cb.a.bc.cb.a.bc"],["a.b.C.bA.AC.Ab.cb.CA.CB","CB.a.a.bA.AC.CB.a.a.bA.AC.CB.a.a.bA.AC.CB.a"],["a.b.C.bA.AC.Ab.cb.CA.BC","bA.AC.a.a.BC.a.BC.bA.AC.a.a.BC.bA.AC.a.a.BC"],["a.b.C.bA.AC.Ab.cb.CA.Ba","AC.Ba.Ba.AC.b.a"],["a.b.C.bA.AC.Ab.cb.CA.B.c.aC","a.a.c.a.c.a.c.a.aC.a.a.c.a.c.a.c.a.aC.a.a.c.a.c.a.c.a.c.a.aC.a.a.c.a.c.a.c.a.aC.a.a.c.a.c.a.c.a.aC.a.aC"],["a.b.C.bA.AC.Ab.cb.CA.B.c.cA","a.a.cA.c.a.a.a.a.cA.c.a.a.a.a.a.a.cA.c.a.a.a.a.cA.c.a.a.a.a.cA.cA.c.a.a.a.a.cA.c.a.a.a.a.cA.c.a.a.a.a"],["a.b.C.bA.AC.Ab.cb.CA.B.c.C.ba","a.B.a.a.ba.a.B.a.B.C.C.ba"],["a.b.C.bA.AC.Ab.cb.CA.B.c.C.AB","AB.C.C.C.B.AB.C.C.C.C.C.C.C.B.AB.B.a.B.C.a.B.C.a.B.C"]],"name":"m007(-4,3)","gens":"a.b.c"}"""


def invert_word(word):
    return word.swapcase()[::-1]

def paths_to_root(claims):
    return [c[0] for c in claims]
        
def tree_ok(claims):
    paths = paths_to_root(claims)
    T = nx.DiGraph()
    T.add_node('1')
    leaves = ['1']
    for path in paths:
        vert = '1'
        for g in path:
            new_vert = vert + '.' + g
            T.add_edge(vert, new_vert, label=g)
            vert = new_vert
        leaves.append(vert)

    # A branching is a directed forest where every vertex has in-degree
    # a most 1.            
    if not nx.is_branching(T):
        return False

    # Now check that the tree is trivalent.
    degrees = T.degree()
    leaf_count = 0
    for v in T.nodes():
        if v in leaves:
            if degrees[v] != 1:
                return False
            leaf_count += 1
        else:
            if degrees[v] != 3:
                return False
            # Check the outgoing edges of this interior vertex
            # labelled by inverse words.
            w0, w1 = [attr['label'] for attr in T.adj[v].values()]
            if invert_word(w0) != w1:
                return False

    # Make sure there wasn't any redundancy in the path data.
    if leaf_count != len(leaves):
        return False

    # This should be redundant, but might as well check. 
    paths_from_root = nx.single_source_shortest_path(T, '1')
    for v, path in paths_from_root.items():
        for p in path:
            if not v.startswith(p):
                return False
    return True
    
    

def all_nontrivial_edge_labels(solver, claims):
    edge_labels = set(sum(paths_to_root(claims), []))
    return all(solver.is_nontrivial(e) for e in edge_labels)

def check_claim(solver, claim):
    path_to_root, trivial_word = claim
    is_one = solver.is_trivial(''.join(trivial_word))    
    valid_words = set(path_to_root)
    return set(trivial_word).issubset(valid_words) and is_one

def check_proof(proof):
    if isinstance(proof, str):
        proof = json.loads(proof)
    M = snappy.Manifold(proof['name'])
    solver = word_problem.WordProblemSolver(M, bits_prec=100,
                                            fundamental_group_args=proof['group_args'])

    # We never actually use these assertions when checking the proof,
    # but it's hard to imagine that we will succeed if they fail.
    assert solver.rho.generators() == proof['gens'].split('.')
    assert solver.rho.relators() == proof['rels']

    claims = proof['proof']
    claims = [(a.split('.'), b.split('.')) for a, b in claims]
    a0 = tree_ok(claims)
    a1 = all_nontrivial_edge_labels(solver, claims)
    a2 = all(check_claim(solver, c) for c in claims)
    return a0 and a1 and a2


def random_proof():
    dir = '/pkgs/tmp/proofs_new/'
    d = os.listdir(dir)
    f = random.choice(d)
    proof = open(dir + f).read()
    print(f, check_proof(proof))

T = check_proof(sample1)
