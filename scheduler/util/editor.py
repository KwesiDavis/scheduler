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
        src - A process-port specification (to receive data from) of the from:
             (srcProcess, srcPort)
        tgt - A process-port specification (to send data to) of the from:
             (tgtProcess, tgtPort)
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
    Apply (or copy) the given edits (or data) to the supplied original graph.
    
    Parameters:
        graph - A graph to modify.
        edits - Some modifications for the given graph.
    '''    
    for key in ['processes', 'inports', 'outports']:
        try:
            # Note: Don't do: graph.setdefault(key, {}).update(edits[key])
            #       That adds the key-value pair before we know if the key
            #       will throw an exception.
            value = edits[key]
        except KeyError:
            pass
        # Only add attributes to the copy that exist in the original
        # ( or only add key-value pair if try succeeds)
        else:
            graph.setdefault(key, {}).update(value)
    for key in ['connections']:
        try:
            # Note: Don't do: graph.setdefault(key, []).extend(edits[key])
            #       That adds the key-value pair before we know if the key
            #       will throw an exception.
            value = edits[key]
        except KeyError:
            pass
        # Only add attributes to the copy that exist in the original
        # ( or only add key-value pair if try succeeds)
        else:
            graph.setdefault(key, []).extend(value)
        
def newGraph():
    '''
    Create a new empty graph.
    
    Returns:
        A dictionary representing a graph. 
        The graph is of the form:
          {'processes':{}, 'inports':{}, 'outports':{}, 'connections':[]}
        
    '''
    return {'processes':{}, 'inports':{}, 'outports':{}, 'connections':[]}

def iip(graph, data, tgt):
    '''
    Specify the given data value should arrive at the given target port at network startup-time.
    
    Parameters:
        graph - A graph to modify. 
        data - The to send at network startup-time
        tgt - A process-port specification (to send data to) of the from:
             (tgtProcess, tgtPort)
    '''
    if issubclass(type(tgt), basestring):
        tgtProcessName, tgtPortName = tgt, 'in'
    else:
        tgtProcessName, tgtPortName = tgt
    connection = { "data" : data, 
                   "tgt"  : { "process" : tgtProcessName,
                              "port"    : tgtPortName } }
    
    graph.setdefault( 'connections', [] ).append(connection)

def export(graph, portName, tgt, isInport=True):
    '''
    Export a new port on the external interface of the given network.  The new
    port will have the given port name and will pipe information packets to (or
    from) the given internal target process-port specification.
    
     Parameters:
        graph - A graph to modify.
        portName - The name of the new port on the external interface.
        tgt - A process-port specification (to send data to) of the from:
             (tgtProcess, tgtPort)              
    '''    
    portType        = { True  : 'inports',
                        False : 'outports' }   
    defaultPortName = { True  : 'in',
                        False : 'out' }
    if issubclass(type(tgt), basestring):
        tgtProcessName, tgtPortName = tgt, defaultPortName[isInport]
    else:
        tgtProcessName, tgtPortName = tgt
    export = { portName : { "process" : tgtProcessName, 
                            "port"    : tgtPortName } }
    graph.setdefault( portType[isInport], {} ).update(export)