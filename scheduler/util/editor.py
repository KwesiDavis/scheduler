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
    process = graph['processes'][processName]
    process.setdefault('metadata', {}).setdefault('config', {}).update(config)

def process( graph, name, componentName, config=None, metadata=None ):
    process = { name : { 'component' : componentName } }
    if metadata:
        process[name]['metadata'] = metadata
    graph.setdefault( 'processes', {} ).update(process)
    # add config data
    if config:
        setConfig(graph, name, config)        

def connection(graph, src, tgt):
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

def apply(graph, edits):
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