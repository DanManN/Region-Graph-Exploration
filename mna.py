from graph_tool.all import *
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
import numpy as np

def equivalent_resistances(g,node_pairs):
    vind = g.new_vertex_property('long')
    c = 0
    for v in g.vertices():
        vind[v] = c
        c += 1
    G = laplacian(g, index=vind)
    Rmap = {}
    for v1,v2 in node_pairs:
        n1 = vind[v1]
        n2 = vind[v2]
        r = G[n2]
        s = r.shape[1]
        diff = csr_matrix((np.append([-1],r.data),np.append([n1],r.indices),[r.indptr[0]]*(n2+1)+[r.indptr[1]+1]*(s-n2)),shape=G.shape)
        diff += diff.transpose()
        diff[n2,n2] = G[n2,n2]
        Gnn = G - diff
        I = csr_matrix(([1],([n2],[0])),shape=(s,1))
        ans = spsolve(Gnn,I)
        Rmap[(v1,v2)] = ans[n1]/ans[n2]
    return Rmap

def equivalent_resistance(g,v1,v2):
    vind = g.new_vertex_property('long')
    c = 0
    for v in g.vertices():
        vind[v] = c
        c += 1
    G = laplacian(g, index=vind)
    n1 = vind[v1]
    n2 = vind[v2]
    r = G[n2]
    s = r.shape[1]
    diff = csr_matrix((np.append([-1],r.data),np.append([n1],r.indices),[r.indptr[0]]*(n2+1)+[r.indptr[1]+1]*(s-n2)),shape=G.shape)
    diff += diff.transpose()
    diff[n2,n2] = G[n2,n2]
    Gnn = G - diff
    I = csr_matrix(([1],([n2],[0])),shape=(s,1))
    ans = spsolve(Gnn,I)
    return ans[n1]/ans[n2]


def getEdgeResistances(graph):
    resistances = graph.new_edge_property('float')
    edges = graph.get_edges()
    Rmap = equivalent_resistances(graph,edges[:,0:2])
    for edge in graph.edges():
        resistances[edge] = Rmap[(int(edge.source()),int(edge.target()))]
    return resistances
