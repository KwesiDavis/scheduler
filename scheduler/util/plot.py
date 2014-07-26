import networkx
from matplotlib import pyplot as plt
import scheduler.component

def connectionInfo(connection):
    '''
    Builds a convenient graph edge representation from the given JSON 
    connection data.   
    
    Parameters:
        connection - A connection loaded from a JSON graph file.
    Returns:
        Tuple of the form (edge, edgeAttributes)
    '''
    srcProcessName = connection['src']['process']
    srcPortName    = connection['src']['port']
    tgtProcessName = connection['tgt']['process']
    tgtPortName    = connection['tgt']['port'] 
    edge           = (srcProcessName, tgtProcessName)
    attr           = (('src',  srcPortName), ('tgt', tgtPortName))
    return edge, attr 

def processInfo(process, networkxId=None):
    '''
    Builds a convenient graph node representation from the given JSON 
    process data.
    
    Parameters:
        process - A process loaded from a JSON graph file.
        networkxId - This node's associated index in a NetworkX graph. 
    Returns:
        A 'dict' of the form {'component':compName, 'isSubNet':bool, 'process':procName}
    '''
    # MAINT: Missing processID (unique in sub-graph), processIDPath (unique in graph), 
    #        processName (can be non-unique and is the GUI displayed name)
    name, info = process
    attr       = { 'component' : info['component'],
                   'isSubNet'  : False,
                   'process'   : name }
    try:
        attr['metadata'] = info['metadata']
    except KeyError:
        # no metadata to add
        pass        
                
    if not networkxId == None:
        attr['networkxId'] = networkxId
    return attr

def json2networkx(jsonGraph, name='*main*'):
    '''
    Constructs a NetworkX graph from the given JSON file.
    
    Parameters:
        jsonGraph - A graph loaded from a JSON file.
        name - The of the network (or root node). 
    Returns:
        A NetworkX graph object.
    '''
    # Create an empty graph
    rootId = 0 
    attr   = { 'component'  : 'Main',
               'isSubNet'   : True,
               'process'    : name,
               'networkxId' : rootId }
    G = networkx.MultiDiGraph(**attr) # support mutiple edges between two nodes

    # Do some bookkeeping
    uniqueJsonNodeID = attr['process']
    jsonId2nxId = { uniqueJsonNodeID : rootId }
    
    # Populate graph with nodes
    for i, process in enumerate(jsonGraph['processes'].items()):
        networkxId = i+1
        attr       = processInfo(process, networkxId=networkxId)
        G.add_node(networkxId, **attr)
        # Do some bookkeeping
        jsonId2nxId[attr['process']]  = attr['networkxId']
    # Populate graph with edges
    for connection in jsonGraph['connections']:
        try:
            edgeInfo, attr = connectionInfo(connection)
        except KeyError:
            continue # skip IIP's    
        srcUniqueJsonNodeID, tgtUniqueJsonNodeID = edgeInfo 
        edge = jsonId2nxId[srcUniqueJsonNodeID], jsonId2nxId[tgtUniqueJsonNodeID]
        G.add_edge(*edge, **dict(attr))
    
    # Define top-level interface
    '''
    G.graph['export'] = []
    
    for exportIter in [jsonGraph['inports'], jsonGraph['outports']]:
        for export in exportIter:
            edgeInfo, attr = exportInfo(connection)
            srcUniqueJsonNodeID, tgtUniqueJsonNodeID = edgeInfo 
            edge = jsonId2nxId[srcUniqueJsonNodeID], jsonId2nxId[tgtUniqueJsonNodeID]
            G.graph['export'].append( (edge, attr) )
    '''
    return G

def networkx2png(G, outFile):
    """
    Given a NetworkX graph creates a PNG image and writes it to the given
    output file path.
    
    Parameters:
        G - A NetworkX graph object.
        outFile - The file path of the output PNG image. 
    """        
    labels = {}
    node_list  = []
    node_color = []        
    
    type2color = {False : 'yellow',
                  True  : 'cyan'}
    for i, node in enumerate(G):
        indx = i+1 # index zero reserved for root node
        node_list.append(node)
        if scheduler.component.isFramework(G.node[indx]['process']):
            node_color.append('red') # special processes
        else:
            node_color.append(type2color[G.node[indx]['isSubNet']])
        labels[node] = G.node[indx]['process']

    #pos = networkx.graphviz_layout(G, prog='dot')
    
    dpiLoRez    = 100
    dpiHiRez    = 450
    scale       = 30
    aLotOfNodes = 25
    numNodes    = len(node_list)
    node_size   = 300 if (numNodes < aLotOfNodes) else int(300/scale)
    font_size   = 6   if (numNodes < aLotOfNodes) else 2
    linewidths  = 1.0 if (numNodes < aLotOfNodes) else (1.0/scale * 3.0)
    width       = 1.0 if (numNodes < aLotOfNodes) else (1.0/scale * 3.0)

    #networkx.draw(G, pos, node_list=node_list, node_color=node_color,
    #              with_labels=True, labels=labels, font_size=font_size, node_size=node_size,
    #              linewidths=linewidths, width=width)
    networkx.draw_spring(G, node_list=node_list, node_color=node_color,
                         with_labels=True, labels=labels, font_size=font_size, node_size=node_size,
                         linewidths=linewidths, width=width)
    
    plt.draw()      
    dpi = dpiLoRez if (numNodes < aLotOfNodes) else dpiHiRez
    plt.savefig(outFile, dpi=dpi)    
    plt.clf() # clear the old plot