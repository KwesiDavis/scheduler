import json

def json2graph(path):
    '''
    Load the given JSON graph file.
    
    Parameters:
        path - A path to a JSON file.
    Returns:
        A dictionary representing a graph of data relationships between the 
        ports of components.
    '''
    f = open(path, "r")
    return json.loads(f.read())

def setConfig( graph, processName, config ):
    '''
    For the given process, in the given graph, set the given configuration data
    in its metadata.   
    
    Parameters:
        graph - a graph to modify 
        processName - the process we wish to configure
        config - the configuration data to add
    '''    
    process = graph['processes'][processName]
    process.setdefault('metadata', {}).setdefault('config', {}).update(config)

def process( graph, name, componentName, config=None, metadata=None ):
    '''
    Add a new process with the given name and the given component type to the supplied graph.   
    
    Parameters:
        graph - A graph to modify. 
        name - The name for the new process.
        componentName - The type of process to instantiate.
        config - Some optional configuration data for the new process.
        metadata - Some optional metadata data for the new process.
    '''    
    process = { name : { 'component' : componentName } }
    if metadata:
        process[name]['metadata'] = metadata
    graph.setdefault( 'processes', {} ).update(process)
    # add config data
    if config:
        setConfig(graph, name, config)        

def connection(graph, src, tgt):
    '''
    Add a new connection, to the supplied graph, with the given source and
    target end-points.   
    
    Parameters:
        graph - A graph to modify. 
        src - An information packet source of the from :(srcProcess, srcPort)
        tgt - An information packet target of the from: (tgtProcess, tgtPort)
    '''    
    if issubclass(type(src), basestring):
        srcProcessName, srcPortName = src, 'out'
    else:
        srcProcessName, srcPortName = src

    if issubclass(type(tgt), basestring):
        tgtProcessName, tgtPortName = tgt, 'in'
    else:
        tgtProcessName, tgtPortName = tgt
    connection = { "src": { "process" : srcProcessName, 
                            "port"    : srcPortName }, 
                   "tgt": { "process" : tgtProcessName,
                            "port"    : tgtPortName } }
    
    graph.setdefault( 'connections', [] ).append(connection)

def modify(graph, edits):
    '''
    Apply the given edits to the supplied graph.
    
    Parameters:
        graph - A graph to modify.
        edits - Some modifications for the given graph.
    '''    
    for key in ['processes', 'inports', 'outports']:
        try:
            graph.setdefault(key, {}).update(edits[key])
        except KeyError:
            pass
    for key in ['connections']:
        try:
            graph.setdefault(key, []).extend(edits[key])
        except KeyError:
            pass