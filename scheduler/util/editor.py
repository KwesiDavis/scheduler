def config( graph, processName, config ):
    process = graph['processes'][processName]
    process.setdefault( 'metadata', {} )['config'] = config

def process( graph, name, componentName, config=None, metadata=None ):
    process = { name : { 'component' : componentName } }
    if metadata:
        process[name]['metadata'] = metadata
    if config:
        config(graph, name, config)        
    graph.setdefault( 'processes', {} ).update(process)

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
    return retval