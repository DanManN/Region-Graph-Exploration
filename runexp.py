#!/usr/bin/env python2
from kcompdecomp import *
from flow import *
from mna import *
from treevis import watchTree
from decompvis import watchdecomp
from app.GraphManager import GraphManager
from random import randint
from math import log10
import sys
import pickle

sys.settrace

def randgraph(N,mindeg,maxdeg):
    return random_graph(N,lambda x:randint(mindeg,maxdeg),directed=False)

args = sys.argv
g = None

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

def loadFile(a):
    global g,glayers,gfilts,ktree,comps,kcomps,ss,cores,resistances,vresistances,posres,volts
    try:
        gm = GraphManager(None)
        g = gm.create_graph(a[1])
    except IndexError:
        print('No file specified. Using random graph instead.')
        g = randgraph(100,1,10)
    except Exception:
        print('Could not load file! Using random graph instead.')
        g = randgraph(100,1,10)

    glayers,gfilts = peel(g)
    ktree = None
    comps = None
    kcomps = None
    ss = None
    cores = []
    resistances = None
    vresistances = None
    posres = None
    volts = None

loadFile(args)

def walk(tree,info):
    if tree is None:
        return
    for child in tree.children:
        if child.children == []:
            g.set_vertex_filter(child.component)
            if info == 'draw':
                graph_draw(g, arf_layout(g))
            elif info == 'order':
                print(g.num_vertices())
            elif info == 'size':
                print(g.num_edges())
            elif info == 'volts':
                maxv = 0
                minv = 1
                for v in g.vertices():
                    if maxv < volts[v]: maxv = volts[v]
                    if minv > volts[v]: minv = volts[v]
                print('max: {}\nmin: {}\nrange:{}'.format(maxv,minv,maxv-minv))
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

while True:
    cmd = raw_input("(k) $ ")
    if cmd in ('quit','q','exit'):
        break
    if cmd == '':
        continue

    parse = cmd.split()
    if parse[0] in ('draw','d'):
        try:
            subg = glayers[int(parse[1])]
            graph_draw(subg, arf_layout(subg))
        except IndexError:
            graph_draw(g, arf_layout(g))
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('sessionsave', 'ss'):
        try:
            save_file = open(parse[1],'wb')
            pickle.dump((g,glayers,gfilts,ktree,comps,kcomps,ss,cores,resistances,vresistances,posres,volts),save_file)
        except IndexError:
            print('Specifiy save file!')
    elif parse[0] in ('sessionload', 'sl'):
        try:
            load_file = open(parse[1],'rb')
            g,glayers,gfilts,ktree,comps,kcomps,ss,cores,resistances,vresistances,posres,volts = pickle.load(load_file)
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
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('size','s'):
        try:
            print(glayers[int(parse[1])].num_edges())
        except IndexError:
            print(g.num_edges())
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('random','r'):
        try:
            g = randgraph(int(parse[1]),int(parse[2]),int(parse[3]))
            glayers,gfilts = peel(g)
        except (IndexError, ValueError) as err:
            print('Specifiy random graph parameters: order, min degree, max degree')
    elif parse[0] in ('kcompdecomp','k'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
        except IndexError:
            pass
        comps = []
        kcomps = g.new_edge_property('int')
        ss = g.new_vertex_property('bool')
        ktree = kcompdecomp(g,array=comps,edge_prop=kcomps,sep_sets=ss)
        g.clear_filters()
    elif parse[0] in ('leaves','lv'):
        try:
            info = parse[1]
        except IndexError:
            info = 'draw'
        walk(ktree,info)
        g.clear_filters()
    elif parse[0] in ('treeview','t'):
        if ktree:
            dynamic = False
            savepng = False
            try:
                if 'd' in parse[1]:
                    dynamic = True
                if 'o' in parse[1]:
                    savepng = True
            except IndexError:
                pass
            watchTree(ktree,ktree.graph,dynamic,offscreen=savepng)
            # watchTree(ktree,ktree.graph,edge_prop=kcomps,posres=posres)
            # watchTree(ktree,ktree.graph,resistances,vresistances,posres)
        g.clear_filters()
    elif parse[0] in ('kview','kv'):
        if comps:
            watchTree(comps,ktree.graph,edge_prop=kcomps,vert_prop=ss,posres=posres)
            # watchTree(comps,ktree.graph,resistances,vresistances,posres)
        g.clear_filters()
    elif parse[0] in ('decompanimation','da'):
        if ktree:
           watchdecomp(ktree)
        g.clear_filters()
    elif parse[0] in ('kcomponentview','kcv'):
        if kcomps:
            g.set_vertex_filter(ktree.component)
            graph_draw(g, arf_layout(g), edge_color=kcomps, vertex_fill_color=ss)
        g.clear_filters()
    elif parse[0] in ('cores','c'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
        cores = middleout(g, resistances)
    elif parse[0] in ('coreview','cv'):
        try:
            info = parse[1]
        except IndexError:
            info = 'draw'
        for c in cores:
            g.set_vertex_filter(c)
            if info == 'draw':
                graph_draw(g, arf_layout(g))
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
        except (ValueError, KeyError) as err:
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
            except (ValueError, KeyError) as err:
                print('No such layer: ' + parse[1])
    elif parse[0] in ('mnadecomp','md'):
        try:
            subg = glayers[int(parse[1])]
            vresistances = mnadecomp(subg)
        except IndexError:
            vresistances = mnadecomp(g)
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
    elif parse[0] in ('mnasort','ms'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except (ValueError, KeyError) as err:
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
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
        volts = nodeVoltages(g)
        posres = g.new_vertex_property('vector<float>')
        x = 0
        for v in g.vertices():
            posres[v] = (x,100*volts[v])
            x += 1
        graph_draw(g, posres)
    elif parse[0] in ('flow','f'):
        try:
            g.set_vertex_filter(gfilts[int(parse[1])])
        except IndexError:
            pass
        except (ValueError, KeyError) as err:
            print('No such layer: ' + parse[1])
        ktree = flowdecomp(g)
