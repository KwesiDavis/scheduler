'''
Parse initial information packets
'''

def addFromGraph(graph):
    iips        = []
    connections = []
    deleteIndex = []
    for i, connection in enumerate( graph['connections'] ):
        # All IIP connection will have data to send.
        try:
            data = connection['data']
        except KeyError:
            # Connections between network processes are handled elsewhere.
            continue
        tgtProcessName = connection['tgt']['process']
        tgtPortName    = connection['tgt']['port']
        # Assume a special IIP process is in the graph; which has out-ports 
        # named after each IIP's target process and target port. 
        srcProcessName = '_iips_' 
        srcPortName    = '{proc}_{port}'.format(proc=tgtProcessName, port=tgtPortName )
        # Build configuration data for the special IIP process.
        iips.append( [data, tgtProcessName, tgtPortName] )
        # Wire the special IIP process into the graph.
        connection = { "src": { "process" : srcProcessName, 
                                "port"    : srcPortName }, 
                       "tgt": { "process" : tgtProcessName,
                                "port"    : tgtPortName } }
        connections.append( connection )
        deleteIndex.append(i)
    deleteIndex.reverse()
    for i in deleteIndex:
        # Remove this iip-as-connection entry
        del graph['connections'][i]
    # Instead of representing IIPs as special connections, we represent them as
    # a special process wired into the network.
    if connections:
        # Create the special IIP process with proper configuration data.
        process = { "_iips_" : { "component" : "_IIPs_", 
                                 "metadata"  : { "config" : iips } } }
        # Update graph with special IIP process
        graph['connections'].extend(connections)
        graph['processes'].update(process) 
    return graph
