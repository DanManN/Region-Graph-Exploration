from graph_tool.all import *
from kcompdecomp import *

def auxiliaryGraph(g):
    auxg = Graph()
    point = g.new_vertex_property('object')
    backpoint = auxg.new_vertex_property('object')
    c = 0
    for v in g.vertices():
        point[v] = auxg.add_edge(2*c,2*c+1)
        backpoint[2*c] = v
        backpoint[2*c+1] = v
        c += 1
    for e in g.edges():
        auxg.add_edge(point[e.source()].target(),point[e.target()].source())
        auxg.add_edge(point[e.target()].target(),point[e.source()].source())
    return auxg, point, backpoint

def min_v_st_cut(g,s,t):
    auxg,point,backpoint = auxiliaryGraph(g)
    cap = auxg.new_edge_property('int',1)
    source = point[t].target()
    target = point[s].source()
    res = edmonds_karp_max_flow(auxg, source, target, cap)
    cut = min_st_cut(auxg, source, cap, res)
    return cut,auxg,point,backpoint

def pseudo_min_v_cut(g):
    if g.num_edges() < 1:
        return []
    comps, hist = label_components(g)
    if len(hist) > 1:
        return []
    treemap = random_spanning_tree(g)
    if min(treemap) > 0:
        return []

    pseudo_d,end_pts = pseudo_diameter(g)
    end_pts = sorted(end_pts, key= lambda v : v.out_degree())
    cut,auxg,point,backpoint = min_v_st_cut(g,end_pts[0],end_pts[1])

    ss = set()
    for e in auxg.edges():
        if cut[e.source()] and not cut[e.target()]:
            ss.add(backpoint[e.target()])
    return list(ss)

def flowdecomp(graph,node=None):
    vfilt, inv = graph.get_vertex_filter()
    if node == None:
        node = kTree(graph,graph.get_vertex_filter()[0])
        flowdecomp(graph,node)
        graph.set_vertex_filter(vfilt,inv)
        return node

    graph.set_vertex_filter(node.component)
    ss = pseudo_min_v_cut(graph)
    comps = split(graph,ss)
    if max(comps) == 0:
        return None
    #graph_draw(graph, vertex_fill_color=split(graph,ss))

    for c in set(comps)-set([-1]):
        comp = graph.new_vertex_property('bool')
        for v in find_vertex(graph,comps,c)+ss:
            comp[v] = True
        node.add_child(kTree(graph,comp))

    for child in node.children:
        flowdecomp(graph,child)
