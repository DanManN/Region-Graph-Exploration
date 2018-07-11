from kcompdecomp import *
import numpy as np
from itertools import combinations
from gi.repository import Gtk, Gdk
import sys

old_src = None
g = None
win = None
win2 = None
dtktree = {}

def watchTree(ktree,graph,dynamic=False,edge_prop=None,vert_prop=None,posres=None,offscreen=False):
    try:
        global old_src, g, win, win2, dtktree

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
                dtktree[c1] = ktree[c1]
                dtktree[c2] = ktree[c2]

            g.set_edge_filter(edges)
            pos = arf_layout(g)  # layout positions
            graph.set_vertex_filter(dtktree[0])
        else:
            def populateG(node,pvertex=None):
                global dtktree
                v = g.add_vertex()
                if pvertex:
                    g.add_edge(v,pvertex)
                dtktree[v] = node
                for child in node.children:
                    populateG(child,v)

            populateG(ktree)
            pos = radial_tree_layout(g,g.vertex(0),r=4)  # layout positions
            graph.set_vertex_filter(dtktree[0].component)

        purple = [0.8, 0, 0.4, 1]
        grey = [0.5, 0.5, 0.5, 1]
        blue = [0.0, 0.2, 0.8, 1]
        green = [0.4, 0.9, 0.0, 1]
        yellow = [1.0, 1.0, 0.0, 1]

        vcolor = g.new_vertex_property("vector<double>")
        for v in g.vertices():
            vcolor[v] = grey

        win = GraphWindow(g, pos, geometry=(1000, 800), vertex_fill_color=vcolor)

        if posres:
            pos2 = posres
        else:
            if dynamic:
                pos2 = arf_layout(graph)
            else:
                pos2 = arf_layout(graph, d=4)

        if vert_prop:
            vcolor2 = vert_prop
        else:
            vcolor2 = graph.new_vertex_property("vector<double>")

        if edge_prop:
            ecolor = edge_prop
        else:
            ecolor = graph.new_edge_property("vector<double>")

        vcolor3 = graph.new_vertex_property("vector<double>")
        win2 = GraphWindow(graph, pos2, geometry=(500, 400), edge_color=ecolor, vertex_fill_color=vcolor2, vertex_color=vcolor3)

        def update_comp(widget, event):
            global old_src, g, win, win2
            src = widget.picked
            if src is None or type(src) == bool:
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
                vcolor[v] = grey
            #vcolor[src] = blue
            if src > 0:
                vcolor[list(src.out_edges())[0].target()] = yellow
            def colordown(v):
                vcolor[v] = purple
                for e in v.in_edges():
                    colordown(e.source())
            colordown(src)
            vcolor[src] = blue
                
            widget.regenerate_surface()
            widget.queue_draw()

            if type(ktree) == list:
                graph.set_vertex_filter(dtktree[src])
            else:
                if src > 0:
                    graph.set_vertex_filter(dtktree[src].parent.component)
                    if not vert_prop:
                        for v in graph.vertices():
                            vcolor2[v] = grey
                    if not edge_prop:
                        for e in graph.edges():
                            ecolor[e] = grey
                    graph.set_vertex_filter(dtktree[src].component)
                    if not edge_prop:
                        for e in graph.edges():
                            ecolor[e] = purple
                    if not vert_prop:
                        for v in graph.vertices():
                            vcolor2[v] = purple
                        for v in dtktree[src].parent.seperating_set:
                            vcolor2[v] = yellow
                        for v in dtktree[src].seperating_set:
                            if vcolor2[v] == yellow:
                                vcolor2[v] = green
                            else:
                                vcolor2[v] = blue
                    graph.set_vertex_filter(dtktree[src].parent.component)
                else:
                    graph.set_vertex_filter(dtktree[src].component)
                    if not edge_prop:
                        for e in graph.edges():
                            ecolor[e] = purple
                    if not vert_prop:
                        for v in graph.vertices():
                            vcolor2[v] = purple
                        for v in dtktree[src].seperating_set:
                            vcolor2[v] = blue

            if dynamic:
                if not posres:
                    arf_layout(graph, pos=pos2, d=2.2)
                win2.graph.fit_to_window(ink=True)
            win2.graph.regenerate_surface()
            win2.graph.queue_draw()

            if offscreen:
                window = widget.get_window()
                pixbuf = Gdk.pixbuf_get_from_window(window, 0, 0, 500, 400)
                pixbuf2 = Gdk.pixbuf_get_from_window(win2.graph.get_window(), 0, 0, 500, 400)
                if dynamic:
                    pixbuf2.savev(r'./screens/treeviewdyn/kcomp%06d.png' % src, 'png', [], [])
                    pixbuf.savev(r'./screens/treeviewdyn/ktree%06d.png' % src, 'png', [], [])
                else:
                    pixbuf2.savev(r'./screens/treeview/kcomp%06d.png' % src, 'png', [], [])
                    pixbuf.savev(r'./screens/treeview/ktree%06d.png' % src, 'png', [], [])

        # Bind the function above as a montion notify handler
        win.graph.connect("button_press_event", update_comp)
        #win.graph.connect("motion_notify_event", no_highlight)

        # We will give the user the ability to stop the program by closing the window.
        win.connect("delete_event", Gtk.main_quit)

        # Actually show the window, and start the main loop.
        win.show_all()
        win2.show_all()
        Gtk.main()

    except KeyboardInterrupt:
        Gtk.main_quit()
        return
