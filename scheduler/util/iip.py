'''
Parse initial information packets
'''
import scheduler.util.editor

def addFromGraph(graph):
    '''
    Supplies the given graph with initial information packets (or IIPs). IIPs 
    are represented in the JSON file as connections (with data but no source 
    process). The IIPs are parsed out of the graph file connections and used to
    build configuration data for a special IIP process that is connected to all
    the targets of the IIP data.   
    
    Parameters:
        graph - A graph to modify.
    ''' 
    # create empty graph to contain edits
    graphEdits     = {}
    iips           = {}
    iipProcessName = '*iips*' 
    for i, connection in enumerate( graph['connections'] ):
        # All IIP connection will have data to send.
        try:
            data = connection['data']
        except KeyError:
            # Connections between network processes are handled elsewhere.
            continue
        tgtProcessName = connection['tgt']['process']
        tgtPortName    = connection['tgt']['port']
        # Our IIP process will have out-ports named after each IIP's 
        # target process/port.
        srcProcessName = iipProcessName 
        srcPortName    = '{proc}_{port}'.format(proc=tgtProcessName, port=tgtPortName )
        # Wire the IIP process into the graph.
        scheduler.util.editor.connection(graphEdits, (srcProcessName, srcPortName), (tgtProcessName, tgtPortName))
        # Build configuration data for the IIP process.
        # Keep track of the connections, in the original graph, that 
        # represented IIP data so we can delete them later.
        iips[i] = [data, tgtProcessName, tgtPortName]
    # Instead of representing IIPs as special connections (that have data 
    # and no source process/port), we represent them as a process with 
    # configuration data that is wired into the network at the IIPs' target
    # process/ports.
    # MAINT: These could potentially clobber existing connections. We may need 
    #        to add a Merge node. When multiple connections are required. 
    if iips:
        # Create the special IIP process with proper 
        # configuration data.
        iipConfig = {'iips' : iips.values() }
        scheduler.util.editor.process(graphEdits, iipProcessName, "_IIPs_", config=iipConfig)
        # Remove IIPs-as-special-connection entries from original graph
        deleteIndex = iips.keys()
        deleteIndex.reverse()
        for i in deleteIndex:
            del graph['connections'][i]
        # Update graph with IIP process attached to the 
        # appropriate processes 
        scheduler.util.editor.modify(graph, graphEdits)
    return graph