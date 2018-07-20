from kcompdecomp import *
import numpy as np
from itertools import combinations
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import sys

old_src = None
g = None
win = None
win2 = None
dtktree = {}
count = 0
filtp = None
filtn = None

def watchdecomp(ktree,graph,dynamic=False,edge_prop=None,vert_prop=None,posres=None,offscreen=False,persistant=False,centered=False,last=None):
    try:
        global old_src, g, win, win2, dtktree, count, filtp, filtn
        old_src = None
        count = 0
        
        g = Graph(directed=True)
        edges = None
        vtext = g.new_vertex_property("string")

        def populateG(node,pvertex=None):
            global dtktree
            v = g.add_vertex()
            if pvertex:
                g.add_edge(pvertex,v)
            dtktree[v] = node
            vtext[v] = str(len(node.seperating_set))
            for child in node.children:
                populateG(child,v)

        populateG(ktree)
        pos = radial_tree_layout(g,g.vertex(0),r=4)  # layout positions
        # if dtktree[0].component:
        #     filt = graph.new_vertex_property('bool')
        #     for v in dtktree[0].component:
        #         filt[v] = True
        #     graph.set_vertex_filter(filt)
        # else:
        #     graph.set_vertex_filter(None)
        if last:
            klist = xrange(last,-1,-1)
        else:
            klist = xrange(g.num_vertices()-1,-1,-1)
        # klist = list(reversed(dfs_iterator(g,0,array=True)))

        purple = [0.8, 0, 0.4, 1]
        grey = [0.5, 0.5, 0.5, 1]
        blue = [0.0, 0.2, 0.8, 1]
        green = [0.4, 0.9, 0.0, 1]
        yellow = [1.0, 1.0, 0.0, 1]
        white = [0, 0, 0, 0]

        vcolor = g.new_vertex_property("vector<double>")
        for v in g.vertices():
            vcolor[v] = grey

        win = GraphWindow(g, pos, geometry=(1000, 800), vertex_fill_color=vcolor, vertex_text=vtext)

        if posres:
            pos2 = posres
        else:
            if dynamic:
                pos2 = arf_layout(graph, d=0.1)
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
        prev = graph.new_edge_property('int')
        win2 = GraphWindow(graph, pos2, geometry=(500, 400), edge_color=ecolor, vertex_fill_color=vcolor2, vertex_color=vcolor3, edge_mid_marker=prev)

        def update_comp():
            global old_src, g, win, win2, count, filtp, filtn
            try:
                src = g.vertex(klist[count])
            except IndexError:
                return False
            if not persistant:
                for v in g.vertices():
                    vcolor[v] = grey
            #vcolor[src] = blue
            #if src > 0:
            #    vcolor[list(src.out_edges())[0].target()] = yellow
            def colordown(v):
                vcolor[v] = purple
                for e in v.out_edges():
                    colordown(e.target())
            colordown(src)

            win.graph.regenerate_surface()
            win.graph.queue_draw()

            filtp = graph.new_vertex_property('bool')
            filtn = graph.new_vertex_property('bool')
            filtold = graph.new_vertex_property('bool')
            filtseps = graph.new_vertex_property('bool')
            vfilt = graph.get_vertex_filter()[0]
            graph.clear_filters()
            for v in graph.vertices():
                filtp[v] = False
                filtn[v] = False
                filtold[v] = False
            if dtktree[src].parent:
                for v in dtktree[src].parent.component:
                    filtp[v] = True
            for v in dtktree[src].seperating_set:
                filtseps[v] = True
            for v in dtktree[src].component:
                filtn[v] = True
            if old_src:
                for v in dtktree[old_src].component:
                    filtold[v] = True
            if persistant and old_src:
                graph.set_vertex_filter(vfilt)
                if not edge_prop:
                    for e in graph.edges():
                        ecolor[e] = grey
                if not vert_prop:
                    for v in graph.vertices():
                        vcolor2[v] = grey
                graph.set_vertex_filter(filtn)
                for v in graph.vertices():
                    vfilt[v] = True
            else:
                vfilt = filtn
                if old_src:
                    for e in graph.edges():
                        prev[e] = 0
                    graph.set_vertex_filter(filtold)
                    for e in graph.edges():
                        prev[e] = 3

            if False: #src > 0:
                graph.set_vertex_filter(filtp)
                if not vert_prop:
                    for v in graph.vertices():
                        vcolor2[v] = grey
                if not edge_prop:
                    for e in graph.edges():
                        ecolor[e] = grey
                graph.set_vertex_filter(filtn)
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
                graph.set_vertex_filter(filtp)
            else:
                graph.set_vertex_filter(filtn)
                if not edge_prop:
                    for e in graph.edges():
                        ecolor[e] = purple
                if not vert_prop:
                    for v in graph.vertices():
                        vcolor2[v] = purple
                if dtktree[src].seperating_set:
                    graph.set_vertex_filter(filtseps)
                    for e in graph.edges():
                        ecolor[e] = yellow
                    for v in dtktree[src].seperating_set:
                        vcolor2[v] = yellow
                    graph.set_vertex_filter(filtn)

            if vfilt:
                graph.set_vertex_filter(vfilt)

            old_src = src

            if dynamic:
                if not posres:
                    arf_layout(graph, pos=pos2, d=2)
                    if centered:
                        center = np.zeros(2)
                        for x in pos2:
                            center += x
                        center /= graph.num_vertices()
                        for v in dtktree[src].seperating_set:
                            pos2[v] = center
                        arf_layout(graph, pos=pos2, d=1, max_iter=6)
                win2.graph.fit_to_window(ink=True)
            win2.graph.regenerate_surface()
            win2.graph.queue_draw()
            if offscreen:
                window = widget.get_window()
                pixbuf = Gdk.pixbuf_get_from_window(window, 0, 0, 1000, 1000)
                pixbuf2 = Gdk.pixbuf_get_from_window(win2.graph.get_window(), 0, 0, 1000, 1000)
                print(src)
                pixbuf2.savev(r'./screens/frames/kcomp%06d.png' % count, 'png', [], [])
                pixbuf.savev(r'./screens/frames/ktree%06d.png' % count, 'png', [], [])
            count += 1
            return True

        # Bind the function above as a montion notify handler
        cid = GObject.idle_add(update_comp)

#        win.graph.connect("button_press_event", update_comp)
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
