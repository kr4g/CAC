import networkx as nx
import hypernetx as hnx
from math import prod
from fractions import Fraction

from allopy.tonos.tonos import octave_reduce

def graph_cps(combos:tuple):
    G = nx.Graph()    
    # each combination is a node (vertex) in the graph
    for combo in combos:
        G.add_node(combo)
    # edges are between nodes that share at least one common factor
    for combo1 in combos:
        for combo2 in combos:
            if combo1 != combo2 and set(combo1).intersection(combo2):
                G.add_edge(combo1, combo2)
    return G

def find_cliques(G:nx.Graph, n:int):
    cliques = nx.enumerate_all_cliques(G)
    return tuple(tuple(clique) for clique in cliques if len(clique) == n)

def combo_clique_to_ratios(clique:tuple, min_prod:int, equave:int=2, n_equaves:int=1):
    return tuple(sorted(octave_reduce(interval  = Fraction(prod(combo), min_prod),
                                      equave    = equave,
                                      n_equaves = n_equaves) for combo in clique))

def hyper_graph_cps(G:nx.Graph, n:int):
    cliques = nx.enumerate_all_cliques(G)
    edges = {}
    for i, clique in enumerate(cliques):
        # if 2 > (n := len(clique)) > 3: continue
        if len(clique) != n: continue
        edges[f'{n}-ad'] = clique
    H = hnx.Hypergraph(edges)
    return H