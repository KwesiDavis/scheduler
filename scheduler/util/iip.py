'''
Merge initial information packets with packets coming from an exported in-port.
'''
import scheduler.util.editor

def addFromGraph(graph):
    '''
    When an IIP connection and an exported in-port connection are both 
    connected to the same internal in-port, we want data to arrive at the 
    target port on a first-come first-serve basis.  The Merge component models 
    this behavior so we insert one.  As a result, the multiple connection lands 
    on the input of the Merge component and its output feeds into the targeted 
    internal in-port. In all other cases, multiple connections are left as-is.
    
    Note: Multiple connections, on an in-port, are not supported, in the 
          general case, because it is difficult to know if the graph author
          wants 'join' or 'merge' behavior at the multiple connection. In this
          case, however, we know the author intends to merge incoming data. 
    
    Parameters:
        graph - A graph to modify.
        
    Returns:
        The modified graph.
    ''' 
    graphEdits  = {}
    target2port = dict([((value['process'], value['port']), key) for key, value in graph['inports'].items()])
    mergeCount  = 0
    for connection in graph['connections']:
        # All IIP connection will have data to send.
        try:
            connection['data']
        except KeyError:
            # Not an IIP so skip it.
            continue
        tgtProcessName = connection['tgt']['process']
        tgtPortName    = connection['tgt']['port']
        try:
            port = target2port[(tgtProcessName, tgtPortName)]
        except KeyError:
            # Not multiple-connection so skip it
            continue
        mergeProcessName = '*merge{index}*'.format(index=str(mergeCount))
        mergeCount += 1
        scheduler.util.editor.process(graphEdits, mergeProcessName, "Merge")
        scheduler.util.editor.connection(graphEdits, (mergeProcessName, 'out'), (tgtProcessName, tgtPortName))
        connection['tgt']['process']      = mergeProcessName
        connection['tgt']['port']         = 'in'
        graph['inports'][port]['process'] = mergeProcessName
        graph['inports'][port]['port']    = 'in'
    scheduler.util.editor.modify(graph, graphEdits)
    return graph