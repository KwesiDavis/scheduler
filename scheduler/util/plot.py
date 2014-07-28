import networkx
from matplotlib import pyplot as plt
import scheduler.component.base

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
                   'isSubNet'  : info['component'] == 'SubNet',
                   'process'   : name }
    try:
        attr['metadata'] = info['metadata']
    except KeyError:
        # no metadata to add
        pass        
                
    if not networkxId == None:
        attr['networkxId'] = networkxId
    return attr

def exportInfo(export, type, root='*main*'):
    '''
    '''
    # Collect the connection data into source and target process/port pairs.
    externalPort, internalInfo = export
    srcIdx,       tgtIdx       = 0, 1
    processIdx,   portIdx      = 0, 1
    connData = [ (root, externalPort), (internalInfo['process'], internalInfo['port']) ]
    # For out-ports, reverse how the connection data is interpreted such that
    # the root is now the target (instead of the source) of the exported 
    # interface connection.
    if type == 'outports':
        connData.reverse()
    conn = { 'src' : { 'process' : connData[srcIdx][processIdx],
                       'port'    : connData[srcIdx][portIdx] },
             'tgt' : { 'process' : connData[tgtIdx][processIdx],
                       'port'    : connData[tgtIdx][portIdx] } }
    return connectionInfo(conn)

#def json2networkx(jsonGraph, name='*main*', root=False):
def json2networkx(jsonGraph, name='*main*', root=False):
    '''
    Constructs a NetworkX graph from the given JSON file.
    
    Parameters:
        jsonGraph - A graph loaded from a JSON file.
        name - The of the network (or root node). 
    Returns:
        A NetworkX graph object.
    '''
    # Build a map from the JSON graph unique node name to the Networkx graph 
    # unique node name.
    jsonId2nxId = {}
    
    # Create a graph root
    rootId = 0 
    attr   = { 'component'  : 'SubNet',
               'isSubNet'   : True,
               'process'    : name,
               'networkxId' : rootId }
    G = networkx.MultiDiGraph(**attr) # support multiple edges between two nodes
    # Put root in the graph as actual-data (in addition to the duplicate 
    # metadata attached to the top-level MultiDiGraph object as attributes.   
    if root:
        # Populate graph with root node
        G.add_node(rootId, **attr)
    # Do some bookkeeping
    jsonId2nxId[attr['process']]  = rootId
    
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
    G.graph['export'] = []
    for type in ['inports', 'outports']:
        for exportItem in jsonGraph[type].items():
            edgeInfo, attr = exportInfo(exportItem, type, root=name)
            srcUniqueJsonNodeID, tgtUniqueJsonNodeID = edgeInfo 
            edge = jsonId2nxId[srcUniqueJsonNodeID], jsonId2nxId[tgtUniqueJsonNodeID]
            # Put connections to root in the graph, as actual-data (in addition
            # to the duplicate metadata attached to the top-level MultiDiGraph 
            # object as the 'export' attribute.   
            if root:
                # Populate graph with edges to the root node
                G.add_edge(*edge, **dict(attr))
            G.graph['export'].append( (edge, attr) )
            
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
    for node in G:
        index = node
        node_list.append(node)
        if scheduler.component.base.isFramework(G.node[index]['process']):
            node_color.append('red') # special processes
        else:
            node_color.append(type2color[G.node[index]['isSubNet']])
        labels[node] = G.node[index]['process']    

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