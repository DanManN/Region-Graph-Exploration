from kcompdecomp import *
import numpy as np
from itertools import combinations
from gi.repository import Gtk, Gdk
import sys

old_src = None
g = None
win = None
win2 = None
dtree = {}

def watchTree(ktree,graph,resistances=None,vresistances=None,posres=None):
    try:
        global old_src, g, win, dtree

        g = Graph(directed=True)
        edges = None

        if type(ktree) == list:
            g.set_directed(False)
            edges = g.new_edge_property('bool')
            for c1,c2 in combinations(range(len(ktree)),2):
                edge = g.add_edge(c1,c2)
                # print(ktree[c1].a)
                # print(ktree[c2].a)
                edges[edge] = np.any(np.logical_and(ktree[c1].a,ktree[c2].a))
                # print(edges[edge])
                dtree[c1] = ktree[c1]
                dtree[c2] = ktree[c2]

            g.set_edge_filter(edges)
            pos = arf_layout(g)  # layout positions
        else:
            def populateG(node,pvertex=None):
                global dtree
                v = g.add_vertex()
                if pvertex:
                    g.add_edge(pvertex,v)
                dtree[v] = node.component
                for child in node.children:
                    populateG(child,v)

            populateG(ktree)

            pos = radial_tree_layout(g,g.vertex(0))  # layout positions

        vcolor = g.new_vertex_property("vector<double>")
        for v in g.vertices():
            vcolor[v] = [0.6, 0.6, 0.6, 1]

        win = GraphWindow(g, pos, geometry=(1000, 800), vertex_fill_color=vcolor)

        orange = [0.807843137254902, 0.3607843137254902, 0.0, 1.0]

        def update_comp(widget, event):
            global old_src, g, win
            src = widget.picked
            if src is None:
                return True
            if isinstance(src, PropertyMap):
                src = [v for v in g.vertices() if src[v]]
                if len(src) == 0:
                    return True
                src = src[0]
            if src == old_src:
                return True
            old_src = src
            for v in g.vertices():
                vcolor[v] = [0.6, 0.6, 0.6, 1]
            vcolor[src]= orange
            widget.regenerate_surface()
            widget.queue_draw()

            graph.set_vertex_filter(dtree[src])
            print(dtree[src].a)
            if posres:
                pos2 = posres
            else:
                pos2 = arf_layout(graph)
            win2 = GraphWindow(graph, pos2, geometry=(500, 400), edge_color=resistances, vertex_fill_color=vresistances)
            win2.show_all()

        # Bind the function above as a montion notify handler
        win.graph.connect("button_press_event", update_comp)

        # We will give the user the ability to stop the program by closing the window.
        win.connect("delete_event", Gtk.main_quit)

        # Actually show the window, and start the main loop.
        win.show_all()
        Gtk.main()
    except KeyboardInterrupt:
        Gtk.main_quit()
        return
