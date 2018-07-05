from graph_tool.all import *
from itertools import combinations
from app.Helpers import kcore_decomposition

def peeldecomp(graph):
    vfilt, inv = graph.get_vertex_filter()
    core = kcore_decomposition(graph)
    kcores = {}
    while len(core) >= 1:
        ind = max(core)
        kcores[ind] = core[ind]
        filt = graph.new_vertex_property('bool', True)
        for v in core[ind]:
            filt[v] = False
        graph.set_vertex_filter(filt)
        core = kcore_decomposition(graph)

    graph.set_vertex_filter(vfilt,inv)
    return kcores

class LayeredBFS(BFSVisitor):

    def __init__(self, name, layers, treemap, pred, deg):
        self.name = name
        self.layers = layers
        self.treemap = treemap
        self.pred = pred
        self.deg = deg

    def discover_vertex(self, u):
        #print("-->", self.name[u], "has been discovered!")
        pass

    def examine_vertex(self, u):
        #print(self.name[u], "has been examined...")
        pass

    def tree_edge(self, e):
        if self.layers:
            self.layers[e.target()] = self.layers[e.source()] + 1
        if self.treemap:
            self.treemap[e] = 2
        if self.pred:
            self.pred[e.target()] = int(e.source())
        if self.deg:
            self.deg[e.target()] = e.target().out_degree()

def split(graph, seperating_set):
    vfilt, inv = graph.get_vertex_filter()
    if vfilt:
        ss = vfilt.copy()
    else:
        ss = graph.new_vertex_property('bool', not inv)
    for v in seperating_set:
        ss[v] = inv
    graph.set_vertex_filter(ss,inv)
    comps, hist = label_components(graph)
    graph.set_vertex_filter(vfilt,inv)
    #print(comps.a)
    for v in seperating_set:
        comps[v] = -1
    return comps

def graphComplement(g):
    edges = {(edge.source(),edge.target()):None for edge in g.edges()}
    for edge in g.edges():
        edges[(edge.target(),edge.source())] = None
    graph = Graph(directed=False)
    for edge in combinations(g.vertices(),2):
        if edge not in edges:
            graph.add_edge(int(edge[0]),int(edge[1]))
    return graph


def pseudo_min_seperating_set(graph):
    if graph.num_edges() < 1:
        return []
    comps, hist = label_components(graph)
    if len(hist) > 1:
        return []

    # top bfs
    pseudo_d, end_pts = pseudo_diameter(graph)
    root = min(end_pts, key= lambda v : v.out_degree())
    layers = graph.new_vertex_property('int')
    treemap = graph.new_edge_property('float', val=0.3)
    #degree = graph.new_vertex_property('int')
    bfs_search(graph, root, LayeredBFS(None, layers, treemap, None, None))#degree))

    # stop if looks like a tree
    if min(treemap) > 1:
        return []

    # middle bfs layer vertices
    max_layer = max(layers)
    middle = [max_layer/2,max_layer/2]
    if max_layer % 2 != 0:
        middle[1] += 1
    vmid = find_vertex_range(graph,layers,middle)

    # smallest bfs layer vertices
    temp = {}
    for l in layers:
        if l not in (0,max_layer):
            temp[l] = temp.get(l, 0) + 1
    if len(temp) > 0:
        minlayer = middle[0]
        mval = temp[minlayer]
        for n in range(middle[0]):
            if middle[1]+n >= max_layer or middle[0]-n <= 0:
                continue
            if mval > temp[middle[1]+n]:
                minlayer = middle[1]+n
                mval = temp[minlayer]
            if mval > temp[middle[0]-n]:
                minlayer = middle[0]-n
                mval = temp[minlayer]
        #minlayer = min(temp, key=temp.get)
        vmin = find_vertex(graph,layers,minlayer)
    else:
        vmin = []

    # bottom bfs
    vbottom = find_vertex(graph,layers,max_layer)
    newroot = min(vbottom, key= lambda v : v.out_degree())
    nlayers = graph.new_vertex_property('int')
    ntreemap = graph.new_edge_property('float', val=0.3)
    #ndegree = graph.new_vertex_property('int')
    bfs_search(graph, newroot, LayeredBFS(None, nlayers, ntreemap, None, None))# ndegree))

    # second middle bfs layer vertices
    nmax_layer = max(nlayers)
    nmiddle = [nmax_layer/2,nmax_layer/2]
    if nmax_layer % 2 != 0:
        nmiddle[1] += 1
    nvmid = find_vertex_range(graph,nlayers,nmiddle)

    # smallest bfs2 layer vertices
    ntemp = {}
    for l in nlayers:
        if l not in (0,nmax_layer):
            ntemp[l] = ntemp.get(l, 0) + 1
    if len(ntemp) > 0:
        nminlayer = nmiddle[0]
        nmval = ntemp[nminlayer]
        for n in range(nmiddle[0]):
            if nmiddle[1]+n >= nmax_layer or nmiddle[0]-n <= 0:
                continue
            if nmval > ntemp[nmiddle[1]+n]:
                nminlayer = nmiddle[1]+n
                nmval = ntemp[nminlayer]
            if nmval > ntemp[nmiddle[0]-n]:
                nminlayer = nmiddle[0]-n
                nmval = ntemp[nminlayer]
        #nminlayer = min(temp, key=temp.get)
        nvmin = find_vertex(graph,nlayers,nminlayer)
    else:
        nvmin = []

    # middle overlap
    overlap = list(set(vmid) & set(nvmid))
    test = graph.new_vertex_property('bool',True)
    for v in overlap:
        test[v] = False

    vfilt, inv = graph.get_vertex_filter()
    graph.set_vertex_filter(test)
    if graph.num_vertices > 0:
        comps, hist = label_components(graph)
    else:
        hist = 0;
    #print('len(hist): '+str(len(hist)))
    if len(hist) <= 1:
        overlap = None
    graph.set_vertex_filter(vfilt,inv)

    # smallest found seperating set
    if overlap:
        ss = min([overlap,vmin,nvmin], key=len)
    else:
        ss = min([vmin,nvmin], key=len)

    # debug
    #print(vmid)
    #print(nvmid)
    #print(overlap==ss)
    #print(vmin)
    #print(degree.a)
    #print(ndegree.a)
    #md = min(set(degree)-set([0]))
    #nmd = min(set(ndegree)-set([0]))
    #for v in graph.vertices():
    #    if degree[v] > md:
    #        degree[v] = -1
    #    else:
    #        degree[v] = 1
    #    if ndegree[v] > nmd:
    #        ndegree[v] = -1
    #    else:
    #        ndegree[v] = 1
    #graph_draw(graph, radial_tree_layout(graph, root), vertex_fill_color=degree, edge_pen_width=treemap)
    #graph_draw(graph, radial_tree_layout(graph, newroot), vertex_fill_color=ndegree, edge_pen_width=ntreemap)

    #print(ss)
    return ss

class kTree(object):
    def __init__(self, graph, component=None, children=None):
        self.graph = graph
        self.component = component
        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)
    def add_child(self, node):
        assert isinstance(node, kTree)
        self.children.append(node)

def kcompdecomp(graph,node=None):
    vfilt, inv = graph.get_vertex_filter()
    if node == None:
        node = kTree(graph,graph.get_vertex_filter()[0])
        kcompdecomp(graph,node)
        graph.set_vertex_filter(vfilt,inv)
        return node

    graph.set_vertex_filter(node.component)
    ss = pseudo_min_seperating_set(graph)
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
        kcompdecomp(graph,child)

def middleout(graph, resistances=None):
    if graph.num_edges() < 1:
        return []

    # top bfs
    pseudo_d, end_pts = pseudo_diameter(graph)
    root = min(end_pts, key= lambda v : v.out_degree())
    layers = graph.new_vertex_property('int')
    treemap = graph.new_edge_property('float', val=0.3)
    degree = graph.new_vertex_property('int')
    bfs_search(graph, root, LayeredBFS(None, layers, treemap, None, degree))

    # stop if looks like a tree
    # if min(treemap) > 1:
    #    return []

    # middle bfs layer vertices
    num_layers = max(layers)+1
    odd = num_layers % 2 != 0
    middle = num_layers/2
    cores = []
    #print('Num_layers: '+str(num_layers))
    #print('Middle: '+str(middle))
    #print(layers.a)
    for l in range(middle+odd):
        verts = find_vertex_range(graph,layers,[middle-l-1+odd,middle+l])
        #print([middle-l-1+odd,middle+l])
        #print(verts)
        filt = graph.new_vertex_property('bool')
        for v in verts:
            filt[v] = True
        cores.append(filt)

    # bottom bfs
    # vbottom = find_vertex(graph,layers,max_layer)
    # newroot = min(vbottom, key= lambda v : v.out_degree())
    # nlayers = graph.new_vertex_property('int')
    # ntreemap = graph.new_edge_property('float', val=0.3)
    # bfs_search(graph, newroot, LayeredBFS(None, nlayers, ntreemap, None, None))

    # second middle bfs layer vertices
    # nmax_layer = max(nlayers)
    # nmiddle = [nmax_layer/2,nmax_layer/2]
    # if nmax_layer % 2 != 0:
    #    nmiddle[1] += 1
    # nvmid = find_vertex_range(graph,nlayers,nmiddle)

    # middle overlap
    # overlap = list(set(vmid) & set(nvmid))
    # test = graph.new_vertex_property('bool',True)
    # for v in overlap:
    #     test[v] = False

    # debug
    #print(vmid)
    #print(nvmid)
    md = min(set(degree)-set([0]))
    for v in graph.vertices():
        if degree[v] > md:
            degree[v] = -1
        else:
            degree[v] = 1
    graph_draw(graph, radial_tree_layout(graph, root), vertex_fill_color=degree, edge_pen_width=treemap, edge_color=resistances)
    #graph_draw(graph, radial_tree_layout(graph, newroot), vertex_fill_color=ndegree, edge_pen_width=ntreemap)

    return cores

def stats(graph):
    cores = kcore_decomposition(graph)
    fixedpoint = len(cores) == 1
    if len(cores) != 0:
        peelvalue = min(cores)
    else:
        peelvalue = 0

    pseudo_d, end_pts = pseudo_diameter(graph)
    root = min(end_pts, key= lambda v : v.out_degree())
    pred = graph.new_vertex_property('int',-1)
    deg = graph.new_vertex_property('int')
    bfs_search(graph, root, LayeredBFS(None, None, None, pred, deg))

    return {'peel_value': peelvalue, 'is_fixed_point': fixedpoint, 'diameter': {'value':pseudo_d, 'path': pred, 'degrees':deg}}
