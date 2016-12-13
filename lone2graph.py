# Emanuele Ruffaldi 2016
import os,sys,re
from collections import defaultdict, OrderedDict
import subprocess, Queue
import argparse
import networkx as nx
import matplotlib.cm
import matplotlib.colors
import matplotlib.pyplot as plt
titles = ["Flight from the Dark","Fire on the Water","The Caverns of Kalte","The Chasm of Doom","Shadow on the Sand","The Kingdoms of Terror","Castle Death"];

def count_dag_paths(ordered,incoming,outgoing,first,last):
    #reverse array from: vertex index to index
    invordered = dict([(ordered[i],i) for i in range(0,len(ordered))])
    lastidx = invordered[last]
    # paths to last
    counts = defaultdict(int)
    counts[last] = 1
    #print ordered
    for i in range(lastidx-1,-1,-1): # index
        ni = ordered[i] 
        q = 0
        for child in outgoing[ni]:
            j = invordered[child]
            if j > i and j <= lastidx:
                q += counts[child] 
        counts[ni] = q 
    return counts

def bfs(graph, start,visited=set()):
    queue = [(start,None)]
    distancefrompath = dict()
    while queue:
        vertex,parent = queue.pop(0)
        if vertex not in visited:
            yield (vertex,parent, True)
            visited.add(vertex)
            queue.extend([(x,vertex) for x in graph[vertex] - visited])
        else:
            yield (vertex,parent, False)

def makedag(o,i,b):
    ro = defaultdict(set)
    ri = defaultdict(set)
    for k,v in o.iteritems():
        ro[k] = v.copy()
    for k,v in i.iteritems():
        ri[k] = v.copy()
    for a,b in b:
        ro[a].remove(b)
        ri[b].remove(a)
    return ro, ri

def analyzeshortest(outgoing,last):
    G = nx.from_dict_of_lists(outgoing,nx.DiGraph())
    try:
        shortest = nx.shortest_path(G,1,last)
    except:
        shortest = []
    return shortest

def analyze(outgoing,incoming,roots,last,backward,booki):

    r = dict()
    visited = set()
    minmax = dict()
    ancestors = defaultdict(set)
    distancefrompath = defaultdict(lambda: 0)
    for ro in roots:
        ancestors[ro] = set()
        for node,parent,isnew in bfs(outgoing,ro,visited):
            if parent is None:
                # except quiz on book 7 
                distancefrompath[node] = 0
            else:
                distancefrompath[node] = distancefrompath[parent]+1
                ancestors[node].add(parent)
                ancestors[node] |= ancestors[parent]

    for parent,children in outgoing.iteritems():
        for c in children:
            if c in ancestors[parent]:
                backward.add((parent,c))
    return r

    # estimate number of paths
    # estimate 

def computedeathscore(booki,incoming_dag,outgoing_dag,ordered,last,randomnodes,pagetype):
    deadscore = dict()
    combatprob = 0.5
    for x in reversed(ordered):
        w = outgoing_dag[x]
        if x == last:
            s = 0.0
        elif len(w) == 0:
            s = 1.0
        else:
            z = randomnodes.get(x)
            anynot1 = len([y for y in w if y < 1]) > 0
            if z is None or len(z["invchoices"]) != len(w):
                n = len(w)
                s = sum([deadscore[y] for y in w])/n
            else:
                invchoices = z["invchoices"]
                # each has to be weighted by the number of cases
                n = z["count"]
                print "book",booki,"node",x,"random",invchoices,"with targets",w
                s = sum([deadscore.get(y,0)*invchoices[y]["count"] for y in w])/n
            if x == 57:
                print "case 57",w,"result",s,"any",anynot1
            if anynot1 and s >= 1:
                s = 0.99
            if "combat" in pagetype[x]:
                if s < combatprob:
                    s = combatprob
        deadscore[x] = s
    return deadscore

# book 7 / page 337 => 0-9 +3
def extractrandom(node,text,target):
    choices = dict()
    invchoices = dict()
    pa = text.split("<p class=\"choice\">")[1:]
    print "xx",node
    for x in pa:
        x = x.split("</p>")[0]
        y = x.split("<a")
        if len(y) != 2:
            continue
        g = re.search(r"(\d+).*?(\d+)",y[0])
        gg = re.search("sect(\d+).htm",y[1])    
        print "\txx",x      
        if g and gg:
            ifrom = int(g.group(1))
            ito = int(g.group(2))
            jmp = int(gg.group(1))
            #print node,ifrom,ito,jmp
        elif gg:
            g = re.search(r"(\d+)",y[0])     
            if g:
                if x.find("or more") >= 0 or x.find("or higher") >= 0:
                    ifrom = int(g.group(1))
                    ito = 9
                    jmp = int(gg.group(1))
                elif x.find("or lower") >= 0 or x.find("or less") >= 0:
                    ito = int(g.group(1))
                    ifrom = 0
                    jmp = int(gg.group(1))
                else:
                    ifrom = int(g.group(1))
                    ito = ifrom
                    jmp = int(gg.group(1))
            else:
                print "\t xx error random",node,"unknown",y[0],g,gg
                return
        else:
            print "\txx error random",node,"unknown",y[0],g,gg
            return
        print "\txx",ifrom,ito,jmp
        for i in range(ifrom,ito+1):
            choices[i] = jmp
        invchoices[jmp] = dict(ifrom=ifrom,ito=ito,count=ito-ifrom+1)
    print "result",choices
    #<p class="choice">TEXT from-to <a href="sect110.htm"> </p>
    if len(choices) > 0:
        target[node] = dict(choices=choices,invchoices=invchoices,count=len(choices))

cmm = None
scm = None
def colormap(value,minv,maxv):
    # colormap is green ... 
    global cmm,scm
    if cmm is None:
        cmm = matplotlib.cm.get_cmap(name="cool", lut=None)
        scm = matplotlib.cm.ScalarMappable(cmap=cmm,norm=matplotlib.colors.Normalize(vmin=minv, vmax=maxv))
    return scm.to_rgba(value,bytes=True)
def color2rgbhex(rgb):
    return "\"#%02X%02X%02X\"" % rgb[0:3]
def main():


    parser = argparse.ArgumentParser(description='Graphs for Lone Wolf')
    parser.add_argument('--outputs',default="pdf png svg")
    parser.add_argument('--outputpath',default="/Users/eruffaldi/Dropbox/Public/lonewolf/")
    parser.add_argument('--inputpath',default="/Users/eruffaldi/Documents/personalfun/lonewolf/xhtml/lw/")
    parser.add_argument('--contentlink',default="https://www.projectaon.org/en/xhtml/lw/")
    parser.add_argument('--clusters',default=0,type=int)
    parser.add_argument('--book',default=-1,type=int)
    args = parser.parse_args()
    #<p class="choice">If you wish to use your Kai Discipline of Sixth Sense, <a href="sect141.htm">turn to 141</a>.</p>
    # files: sect#.htm
    #/Users/eruffaldi/Downloads/en/xhtml/

    #for x in os.listdir(sys.argv[1]):
    #   if x.startswith("sect") and x.endswith(".htm"):

    outputs = args.outputs.split(" ")
    output = args.outputpath
    input = args.inputpath
    link=args.contentlink
    clusters = args.clusters != 0
    print "Cluster Mode",args.clusters

    oo = open("script.sh","w")
    booki = 0
    if clusters:
        outname = os.path.join(input,"all"+".dot")
        print "generating",outname
        outfile = open(outname,"wb")
        outfile.write("digraph G {\n")

    bookplots = []
    bookplots_names = []
    allstats = []
    for dirname in os.listdir(input):
        fx = os.path.join(input,dirname)
        if not os.path.isdir(fx):
            continue
        booki += 1
        if args.book != -1 and args.book != booki:
            continue
        if not clusters:
            outname = os.path.abspath(os.path.join(input,dirname+".dot"))
            print "generating",outname
            outfile = open(outname,"wb")
            outfile.write("digraph G {\n")
        else:
            outfile.write("subgraph cluster_%d {\n" % booki)
        outfile.write("\tlabel=\"%s\"\n" % titles[booki-1])

        allpairs = OrderedDict()
        incoming = defaultdict(set)
        outgoing = defaultdict(set)
        sommer = set()
        pagetype = defaultdict(set)
        pagelink = dict()   
        ancestors = defaultdict(set)
        randomnodes = dict()
        for i in range(1,500):
                #name = int(x[4:-4])
                name = "sect%d.htm" % i
                fp = os.path.join(fx,name)
                if not os.path.isfile(fp):
                    break
                pagelink[i] = name #os.path.abspath(fp)
                y = open(fp,"rb").read()
                if y.find("COMBAT SKILL") >= 0 and y.find("ENDURANCE") >= 0:
                    pagetype[i].add("combat")
                if y.find("Sommerswerd") >= 0:
                    sommer.add(i)
                israndom = (y.find("If your total is") >= 0 or y.find("If the number you have picked is") >= 0) and y.find("Random") >= 0
                if israndom:
                    extractrandom(i,y,randomnodes)

                for p in re.findall("<a href=\"sect(\d+)\.htm\">",y):
                    p = int(p)
                    allpairs[(i,p)] = 1
                    incoming[p].add(i)
                    outgoing[i].add(p)
                    ancestors[p] |= ancestors[i]
        last = i-1



        if booki == 5:
            special = [(331,373)]
            for x,y in special:
                incoming[y].add(x)
                outgoing[x].add(y)
                allpairs[(x,y)] = 1
        elif booki == 7:
            special = [(100,34)]
            for x,y in special:
                incoming[y].add(x)
                outgoing[x].add(y)
                allpairs[(x,y)] = 1

        # we want to estimate if an edge is backward, that is a given page (node) goes back to another 
        # one that has been visited earlier
        backward = set()
        roots = [i for i in range(1,last+1) if len(incoming[i]) == 0]


        s = analyze(outgoing,incoming,roots,last,backward,booki)
        s["book"] = booki

        outgoing_norandom = dict([(k,v) for k,v in outgoing.iteritems() if k not in randomnodes])
        shortest = analyzeshortest(outgoing_norandom,last)
        if len(shortest) == 0:
            shortest = analyzeshortest(outgoing,last)
            s["mindist"] = -len(shortest)
        else:
            s["mindist"] = len(shortest)
        allstats.append(s)
        outgoing_dag,incoming_dag = makedag(outgoing,incoming,backward)
        print "shortest:"

        print "apply shortest",len(shortest)
        for i in range(1,len(shortest)):
            allpairs[(shortest[i-1],shortest[i])] = 2
        # TBD print "book",booki,dirname,s
        dg = nx.from_dict_of_lists(outgoing_dag,nx.DiGraph())
        if not nx.is_directed_acyclic_graph(dg):
            # special
            if booki == 2:
                for a,b in [(15,244),(172,64)]:
                    outgoing_dag[a].remove(b)
                    dg.remove_edge(a,b)
            elif booki == 6:
                for a,b in [(105,79)]:
                    outgoing_dag[a].remove(b)
                    dg.remove_edge(a,b)
            print "cycles",list(nx.simple_cycles(dg))
        if nx.is_directed_acyclic_graph(dg):
            ordered = nx.topological_sort(dg);
            #invordered = dict([(x,i) for i,x in ordered])

            # topological sort
            cp = count_dag_paths(ordered,incoming_dag,outgoing_dag,1,last)
            totalpaths = cp[1]
            s["totalpaths"] = totalpaths
            if False:
                # Something for estimating the mandatory nodes, actually few of them 
                necessarynodes = set([k for k,v in cp.iteritems() if v >= totalpaths])
                necessarynodes.remove(1)
                s["needednodes1"] = len(necessarynodes)
                necessarynodes = set()
                for c in outgoing[1]:
                    totalpathsc = cp[c]
                    necessarynodesc = set([k for k,v in cp.iteritems() if v >= totalpathsc])
                    necessarynodes |= necessarynodesc
                s["needednodes2"] = len(necessarynodes)        

            deadscore = computedeathscore(booki,incoming_dag,outgoing_dag,ordered,last,randomnodes,pagetype)
            print "allthis",list(deadscore.iteritems())
            print deadscore[1]
        else:
            deadscore = {}
            if False:
                incoming = incoming_dag
                outgoing = outgoing_dag
                for a,b in backward:
                    del allpairs[(a,b)]
            s["totalpaths"] = 0
            s["needednodes1"] = 0
            s["needednodes2"] = 0


        if len(deadscore) > 0 and len(shortest) > 0:
            ts = range(0,len(shortest))
            bookplots.append(plt.plot(ts,[deadscore[x] for x in shortest])[0])
            bookplots_names.append("Book %d" % booki)
            plt.ylabel('Death probability')
            plt.xlabel('Steps in shortest')
            # only combat steps
            tsc = [istep for istep in ts if "combat" in pagetype[shortest[istep]]]
            plt.scatter(tsc,[deadscore[shortest[istep]] for istep in tsc],marker="*",c="r")
            outpathdead = os.path.abspath(os.path.join(output,dirname+".shortest.png"))
            plt.legend(bookplots,bookplots_names)
            print "making",outpathdead
            plt.savefig(outpathdead, format='png')

        pagedict = defaultdict(dict)
        for i in range(2,last):
            o = outgoing[i]
            ww = dict()
            if "combat" in pagetype[i]:
                ww["shape"] = "tripleoctagon"
                ww["fillcolor"] = "orange"
                ww["style"] = "filled"
                if i in sommer:
                    ww["fillcolor"] = "magenta"
                else:
                    ww["fillcolor"] = "orange"
            else:
                ww["shape"] = "circle"
            if len(o) == 0:
                ww["fillcolor"] = "red"
                ww["style"] = "filled"
                ww["shape"] = "Mcircle"
            elif len(incoming[i]) == 0:
                ww["fillcolor"] = "green"
                ww["style"] = "filled"
            pagedict[i].update(ww)

        # THE ONLY non dead end
        if booki == 3:
            pagedict[61]["fillcolor"] = "orange"

        for i in range(1,last+1):
            pagedict[i]["label"] = "\"%d\"" % i #/%d/%d\"" % (i,distancefromroot[i],maxincoming[i])
            pagedict[i]["URL"] = "\"%s/%s/%s\"" % (link,dirname,pagelink[i])
            pagedict[i]["target"] = "_blank"

        pagedict[1].update(dict(fillcolor="green",style="filled"))
        pagedict[last].update(dict(fillcolor="green",style="filled"))

        for i in range(1,last+1):
            ww = pagedict[i]
            if len(ww) > 0:
                outfile.write(" b%dp%d [%s];\n" % (booki,i,",".join(["%s=%s" % (x,y) for x,y in ww.iteritems()])))

        for k,v in allpairs.iteritems():
            pfrom,pto = k
            sw = {}
            if (pfrom,pto) in backward:
                sw["arrowhead"] = "inv"
                sw["arrowtail"] = "inv"
            else:
                ww = deadscore.get(pto)
                if ww is not None:
                    ##%2x%2x%2x
                    sw["color"] = color2rgbhex(colormap(ww,0.0,1.0))
                    sw["label"] = "\"%0.3f\"" % ww

            if v == 2:
                sw["penwidth"] =3.0
            if pfrom in randomnodes:
                sw["style"] = "dashed"
            outfile.write("b%dp%d -> b%dp%d [%s];\n" % (booki,pfrom,booki,pto,",".join(["%s=%s" % (x,y) for x,y in sw.iteritems()])))

        outfile.write("}\n")

        if not clusters:
            for t in outputs:
                oo.write(" ".join(["dot", "-T" + t,outname,"-o"+os.path.join(output,dirname+"."+t)])+"\n")
            #subprocess.call(["dot", "-T" + t,outname,"-o"+os.path.join(output,dirname+"."+t)],shell=True)
    if clusters:
        outfile.write("}\n")
        for t in outputs:
            oo.write(" ".join(["dot", "-T" + t,outname,"-o"+os.path.join(output,dirname+"."+t)])+"\n")

    print "created script.sh"
    oo.close()
    if True:
        print "\t".join(["Book","Shortest","Total Paths"])
        for i,a in enumerate(allstats):
            print "%d\t%d\t%d" % (a["book"],a["mindist"],a["totalpaths"]) #,a["maxdist"])

if __name__ == '__main__':
    main()
