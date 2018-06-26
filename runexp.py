#!/usr/bin/env python2
from kcompdecomp import *
from mna import *
from treevis import watchTree
from app.GraphManager import GraphManager
from random import randint
from math import log10
import sys
import pickle

sys.settrace

def randgraph(N,mindeg,maxdeg):
    return graph_tool.generation.random_graph(N,lambda x:randint(mindeg,maxdeg),directed=False)

args = sys.argv
g = None

def loadFile(a):
    global g
    try:
        gm = GraphManager(None)
        g = gm.create_graph(a[1])
    except IndexError:
        print('No file specified. Using random graph instead.')
        g = randgraph(100,1,10)
    except Exception:
        print('Could not load file! Using random graph instead.')
        g = randgraph(100,1,10)

loadFile(args)

def peel(graph):
    kd = peeldecomp(graph)
    layers = {}
    filts = {}
    for layer,vertices in kd.iteritems():
        vfilt = g.new_vertex_property('bool')
        for v in vertices:
            vfilt[int(v)] = True
        layers[layer] = GraphView(g, vfilt)
        filts[layer] = vfilt
    return layers,filts

def walk(tree,info):
    if tree is None:
        return
    for child in tree.children:
        if child.children == []:
            g.set_vertex_filter(child.component)
            if info == 'draw':
                pos = graph_tool.draw.arf_layout(g)
                graph_draw(g, pos)
            elif info == 'order':
                print(g.num_vertices())
            elif info == 'size':
                print(g.num_edges())
        else:
            if info == 'stats':
                g.set_vertex_filter(tree.component)
                d = stats(g)['diameter']
                print('pseudo_d: ' + str(d['value']))
                #print('path: ' + str(d['path'].a))
                #print('degress: ' + str(d['degrees'].a))
                degs = d['degrees'].a
                degs = filter(lambda x:x!=0,degs)
                print('degrees:\nmin:{}\tavg:{}\tmax:{}\n'.format(min(degs),sum(degs)/len(degs),max(degs)))
            walk(child,info)
    g.clear_filters()

glayers,gfilts = peel(g)
ktree = None
cores = []
resistances = None
vresistances = None
posres = None

while True:
    cmd = raw_input("(k) $ ")
    if cmd in ('quit','q'):
        break

    parse = cmd.split()
    if parse[0] in ('draw','d'):
        try:
            subg = glayers[int(parse[1])]
            pos = graph_tool.draw.arf_layout(subg)
            graph_draw(subg, pos)
        except IndexError:
            pos = graph_tool.draw.arf_layout(g)
            graph_draw(g, pos)
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('sessionsave', 'ss'):
        try:
            save_file = open(parse[1],'wb')
            pickle.dump((g,glayers,gfilts,ktree,cores,resistances,vresistances,posres),save_file)
        except IndexError:
            print('Specifiy save file!')
    elif parse[0] in ('sessionload', 'sl'):
        try:
            load_file = open(parse[1],'rb')
            g,glayers,gfilts,ktree,cores,resistances,vresistances,posres = pickle.load(load_file)
        except IndexError:
            print('Specifiy save file!')
    elif parse[0] in ('load', 'ld'):
        loadFile(parse)
        glayers,gfilts = peel(g)
    elif parse[0] in ('layers','ly'):
        print(glayers.keys())
    elif parse[0] in ('order','o'):
        try:
            print(glayers[int(parse[1])].num_vertices())
        except IndexError:
            print(g.num_vertices())
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('size','s'):
        try:
            print(glayers[int(parse[1])].num_edges())
        except IndexError:
            print(g.num_edges())
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('random','r'):
        try:
            g = randgraph(int(parse[1]),int(parse[2]),int(parse[3]))
            glayers,gfilts = peel(g)
        except IndexError, ValueError:
            print('Specifiy random graph parameters: order, min degree, max degree')
    elif parse[0] in ('kcompdecomp','k'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
        ktree = kcompdecomp(g)
    elif parse[0] in ('leaves','lv'):
        try:
            info = parse[1]
        except IndexError:
            info = 'draw'
        walk(ktree,info)
        g.clear_filters()
    elif parse[0] in ('treeview','t'):
        if ktree:
            watchTree(ktree,resistances,vresistances,posres)
        g.clear_filters()
    elif parse[0] in ('cores','c'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
        cores = middleout(g, resistances)
    elif parse[0] in ('coreview','cv'):
        try:
            info = parse[1]
        except IndexError:
            info = 'draw'
        for c in cores:
            g.set_vertex_filter(c)
            pos = graph_tool.draw.arf_layout(g)
            if info == 'draw':
                graph_draw(g, pos)
            elif info == 'stats':
                stat = stats(g)
                print('peel_value: ' + str(stat['peel_value']))
                print('fixed_point?: ' + str(stat['is_fixed_point']))
        g.clear_filters()
    elif parse[0] in ('equiresistance','er'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
        resistances = getEdgeResistances(g)
        g.clear_filters()
    elif parse[0] in ('equiresistanceview','erv'):
        if resistances:
            try:
                subg = glayers[int(parse[1])]
                graph_draw(subg, arf_layout(subg), edge_color=resistances)
            except IndexError:
                graph_draw(g, arf_layout(g), edge_color=resistances)
            except ValueError, KeyError:
                print('No such layer: ' + parse[1])
    elif parse[0] in ('mnadecomp','md'):
        try:
            subg = glayers[int(parse[1])]
            vresistances = mnadecomp(subg)
        except IndexError:
            vresistances = mnadecomp(g)
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('mnasort','ms'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
        ressort = getVertexResistances(g)
        posres = g.new_vertex_property('vector<float>')
        x = 0
        for v in g.vertices():
            posres[v] = (x,1000*round(ressort[v],3))
            x += 1
        graph_draw(g, posres)
        g.clear_filters()
    elif parse[0] in ('voltagesort','vs'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except ValueError, KeyError:
            print('No such layer: ' + parse[1])
        voltsort = nodeVoltages(g)
        posres = g.new_vertex_property('vector<float>')
        x = 0
        for v in g.vertices():
            posres[v] = (x,100*voltsort[v])
            x += 1
        graph_draw(g, posres)
