# Emanuele Ruffaldi 2016
import os,sys,re
from collections import defaultdict, OrderedDict
import subprocess, Queue
import argparse

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

def analyze(outgoing,incoming,roots,last,backward,booki):
    r = dict()
    visited = set()
    minmax = dict()
    ancestors = defaultdict(set)
    distancefrompath = defaultdict(lambda: 0)
    shortestpath = defaultdict(lambda: 0)
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

    for node,parents in incoming.iteritems():
        if len(parents) == 0:
            shortestpath[node] = 0
        else:
            shortestpath[node] = min([distancefrompath[x] for x in parents])
    for parent,children in outgoing.iteritems():
        for c in children:
            if c in ancestors[parent]:
                backward.add((parent,c))
    # then estimate for last
    r["mindist"] = shortestpath[last]
    if False:
        out = []
        current = 1
        while True:
            if len(outgoing[current]) == 0:
                break
            j,v = min([(x,shortestpath[x]) for x in outgoing[current]],key=lambda x: x[1])
            current = j
            out.append(j)
        print "----"
        print "last",last
        print "distancefrompath\n",distancefrompath
        print "shortestpath\n",shortestpath
        print r
        print "shortest",len(out),"done:",out
        print "----"
    return r

    # estimate number of paths
    # estimate 

def main():


    parser = argparse.ArgumentParser(description='Graphs for Lone Wolf')
    parser.add_argument('--outputs',default="pdf png svg")
    parser.add_argument('--outputpath',default="/Users/eruffaldi/Dropbox/Public/lonewolf/")
    parser.add_argument('--inputpath',default="/Users/eruffaldi/Downloads/en/xhtml/lw/")
    parser.add_argument('--contentlink',default="https://www.projectaon.org/en/xhtml/lw/")
    parser.add_argument('--clusters',default=0,type=int)
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
        outfile = open(outname,"wb")
        outfile.write("digraph G {\n")

    allstats = []
    for dirname in os.listdir(input):
        fx = os.path.join(input,dirname)
        if not os.path.isdir(fx):
            continue
        booki += 1
        if not clusters:
            outname = os.path.abspath(os.path.join(input,dirname+".dot"))
            outfile = open(outname,"wb")
            outfile.write("digraph G {\n")
        else:
            outfile.write("subgraph cluster_%d {\n" % booki)


        allpairs = OrderedDict()
        incoming = defaultdict(set)
        outgoing = defaultdict(set)
        sommer = set()
        pagetype = defaultdict(set)
        pagelink = dict()   
        ancestors = defaultdict(set)
        for i in range(1,500):
                #name = int(x[4:-4])
                name = "sect%d.htm" % i
                fp = os.path.join(fx,name)
                if not os.path.isfile(fp):
                    break
                pagelink[i] = name #os.path.abspath(fp)
                y = open(fp,"rb").read()
                if y.find("COMBAT SKILL") >= 0:
                    pagetype[i].add("combat")
                if y.find("Sommerswerd") >= 0:
                    sommer.add(i)
                for p in re.findall("<a href=\"sect(\d+)\.htm\">",y):
                    p = int(p)
                    allpairs[(i,p)] = True
                    incoming[p].add(i)
                    outgoing[i].add(p)
                    ancestors[p] |= ancestors[i]
        last = i-1

        # we want to estimate if an edge is backward, that is a given page (node) goes back to another 
        # one that has been visited earlier
        backward = set()
        roots = [i for i in range(1,last+1) if len(incoming[i]) == 0]
        s = analyze(outgoing,incoming,roots,last,backward,booki)
        allstats.append(s)
        # TBD print "book",booki,dirname,s

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

        for pfrom,pto in allpairs.keys():

            # backward in story means, that if there is any path from to..from earlier
            if (pfrom,pto) in backward:
                outfile.write("b%dp%d -> b%dp%d [color=red];\n" % (booki,pfrom,booki,pto));
            else:
                outfile.write("b%dp%d -> b%dp%d;\n" % (booki,pfrom,booki,pto))
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
    if False:
        print "%s\t%s" % ("Book","Min Path")
        for i,a in enumerate(allstats):
            print "%d\t%d" % (i+1,a["mindist"]) #,a["maxdist"])

if __name__ == '__main__':
    main()
