#! /usr/bin/env python2
from graph_tool.all import *
import time
import os

# We need some Gtk and gobject functions
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

def watchdecomp(ktree,offscreen=False):
    g = ktree.graph
    pos = arf_layout(g)  # initial layout positions

    steps = [ktree]
    def dfs(node):
        global steps
        steps.append(node)
        for child in node.children:
            dfs(node)

    print(steps)

    max_count = len(steps)

    # If True, the frames will be dumped to disk as images.
    if offscreen and not os.path.exists("./frames"):
        os.mkdir("./frames")

    # This creates a GTK+ window with the initial graph layout
    if not offscreen:
        win = GraphWindow(g, pos, geometry=(500, 400))
    else:
        win = Gtk.OffscreenWindow()
        win.set_default_size(500, 400)
        win.graph = GraphWidget(g, pos)
        win.add(win.graph)

    count = 0
    # This function will be called repeatedly by the GTK+ main loop, and we use it
    # to update the vertex layout and perform the rewiring.
    def update_state():
        global steps, count, g

        g.set_vertex_filter(steps[count].component)

        # The movement of the vertices may cause them to leave the display area. The
        # following function rescales the layout to fit the window to avoid this.
        win.graph.fit_to_window(ink=True)

        # The following will force the re-drawing of the graph, and issue a
        # re-drawing of the GTK window.
        win.graph.regenerate_surface()
        win.graph.queue_draw()

        # if doing an offscreen animation, dump frame to disk
        if offscreen:
            pixbuf = win.get_pixbuf()
            pixbuf.savev(r'./frames/decomp%06d.png' % count, 'png', [], [])
            if count >= max_count:
                sys.exit(0)
        else:
            time.sleep(1)

        # We need to return True so that the main loop will call this function more
        # than once.
        return True


    # Bind the function above as an 'idle' callback.
    cid = GObject.idle_add(update_state)

    # We will give the user the ability to stop the program by closing the window.
    win.connect("delete_event", Gtk.main_quit)

    # Actually show the window, and start the main loop.
    win.show_all()
    Gtk.main()
