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

def flowdecomp(graph,node=None,array=None,edge_prop=None,sep_sets=None, max_depth=500, depth = 0):
    vfilt, inv = graph.get_vertex_filter()
    if node == None:
        node = kTree(graph,graph.get_vertices())
        flowdecomp(graph,node,array,edge_prop,sep_sets, max_depth)
        graph.set_vertex_filter(vfilt,inv)
        return node

    # print(node.component)
    if node.component:
        graph.clear_filters()
        nodefilt = graph.new_vertex_property('bool')
        for v in node.component:
            nodefilt[v] = True
        graph.set_vertex_filter(nodefilt)
    else:
        graph.set_vertex_filter(None)
    ss = pseudo_min_v_cut(graph)
    node.set_seperating_set(ss)
    comps = split(graph,ss)
    if sep_sets:
        for s in ss:
            sep_sets[s] = True
    if max(comps) == 0:
        if array is not None: array.append(node.component)
        if edge_prop is not None:
            knum = max(edge_prop.a)+1
            for edge in graph.edges():
                edge_prop[edge] = knum
        return None
    #graph_draw(graph, vertex_fill_color=split(graph,ss))
    if depth+1 >= max_depth:
        return None

    for c in set(comps)-set([-1]):
        comp = set(find_vertex(graph,comps,c))^set(ss)
        # print(comp)
        node.add_child(kTree(graph,comp,node))

    for child in node.children:
        flowdecomp(graph,child,array,edge_prop,sep_sets, max_depth, depth+1)
