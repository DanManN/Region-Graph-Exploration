from kcompdecomp import *
from gi.repository import Gtk, Gdk
import sys

old_src = None
g = None
win = None
win2 = None
dtree = {}

def watchTree(ktree):
    try:
        global old_src, g, win, dtree

        g = Graph(directed=True)

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

            ktree.graph.set_vertex_filter(dtree[src])
            pos2 = arf_layout(ktree.graph)
            win2 = GraphWindow(ktree.graph, pos2, geometry=(500, 400))
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
