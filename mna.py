from graph_tool.all import *
from scipy.sparse import *
from scipy.sparse.linalg import lsqr
from itertools import izip
from kcompdecomp import LayeredBFS
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
        if n1 == n2:
            continue
        r = G[n2]
        s = r.shape[1]
        diff = csr_matrix((np.append([-1],r.data),np.append([n1],r.indices), np.append(np.full(n2+1,r.indptr[0]),np.full(s-n2,r.indptr[1]+1))),shape=G.shape)
        diff += diff.transpose()
        diff -= csr_matrix(([G[n2,n2]],([n2],[n2])),shape=G.shape)
        Gnn = G - diff
        I = np.zeros(s)
        I[n2] = 1
        ans = lsqr(Gnn,I)[0]
        res = -ans[n1]/ans[n2]
        if res < 0:
            Rmap[(v1,v2)] = np.inf
        else:
            Rmap[(v1,v2)] = res
    return Rmap


def equivalent_resistance(g,v1,v2):
    if v1 == v2:
        return 0
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
    diff = csr_matrix((np.append([-1],r.data),np.append([n1],r.indices), np.append(np.full(n2+1,r.indptr[0]),np.full(s-n2,r.indptr[1]+1))),shape=G.shape)
    diff += diff.transpose()
    diff -= csr_matrix(([G[n2,n2]],([n2],[n2])),shape=G.shape)
    Gnn = G - diff
    I = np.zeros(s)
    I[n2] = 1
    ans = lsqr(Gnn,I)[0]
    res = -ans[n1]/ans[n2]
    if res < 0:
        return np.inf
    else:
        return res

def getEdgeResistances(graph):
    resistances = graph.new_edge_property('float')
    edges = graph.get_edges()
    Rmap = equivalent_resistances(graph,edges[:,0:2])
    for edge in graph.edges():
        resistances[edge] = Rmap[(int(edge.source()),int(edge.target()))]
    return resistances

def getVertexResistances(graph):
    resistances = graph.new_vertex_property('float')
    edges = graph.get_edges()
    Rmap = equivalent_resistances(graph,edges[:,0:2])
    for vertex in graph.vertices():
        minr = 1
        for v in vertex.all_neighbors():
            try:
                res = Rmap[(int(vertex),int(v))]
            except KeyError:
                try:
                    res = Rmap[(int(v),int(vertex))]
                except KeyError:
                    res = 1
            if res < minr:
                minr = res
        resistances[vertex] = minr
    return resistances

def mnadecomp(graph):
    pseudo_d, end_pts = graph_tool.topology.pseudo_diameter(graph)
    root = min(end_pts, key= lambda v : v.out_degree())
    treemap = graph.new_edge_property('float', val=0.3)
    graph_tool.search.bfs_search(graph, root, LayeredBFS(None, None, treemap, None, None))
    vert_pairs = izip(np.full(graph.num_vertices(),root),graph.vertices())
    Rmap = equivalent_resistances(graph, vert_pairs)
    resistances = graph.new_vertex_property('float')
    for vp,res in Rmap.iteritems():
        vr,v = vp
        resistances[v] = res

    graph_draw(graph, radial_tree_layout(graph, root), edge_pen_width=treemap, vertex_fill_color=resistances)
    return resistances

def nodeVoltages(g):
    vind = g.new_vertex_property('long')
    c = 0
    for v in g.vertices():
        vind[v] = c
        c += 1
    G = laplacian(g, index=vind)
    pseudo_d, end_pts = graph_tool.topology.pseudo_diameter(g)
    n1 = vind[end_pts[0]]
    n2 = vind[end_pts[1]]
    r = G[n2]
    s = r.shape[1]
    diff = csr_matrix((np.append([-1],r.data),np.append([n1],r.indices), np.append(np.full(n2+1,r.indptr[0]),np.full(s-n2,r.indptr[1]+1))),shape=G.shape)
    diff += diff.transpose()
    diff -= csr_matrix(([G[n2,n2]],([n2],[n2])),shape=G.shape)
    Gnn = G - diff
    I = np.zeros(s)
    I[n2] = 1
    ans = lsqr(Gnn,I)[0]
    voltages = g.new_vertex_property('float')
    for v in g.vertices():
        voltages[v] = ans[vind[v]]
    voltages[end_pts[1]] = 0
    return voltages
