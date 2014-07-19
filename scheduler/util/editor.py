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

def combine(graphA, graphB):
    retval = {}
    retval.update(graphA) 
    for key in ['processes', 'inports', 'outports']:
        try:
            retval.setdefault(key, {}).update(graphB[key])
        except KeyError:
            pass
    for key in ['connections']:
        try:
            retval.setdefault(key, []).extend(graphB[key])
        except KeyError:
            pass
    return retval