'''
Synchronize user input with the start of a process
'''

import scheduler.util.editor

def add(graph):
    # create empty graph to contain edits
    graphEdits = {}
    # add processes    
    scheduler.util.editor.process(graphEdits, '*events*' , 'Merge')
    scheduler.util.editor.process(graphEdits, '*stdin*'  , '_StdIn_')
    scheduler.util.editor.process(graphEdits, '*sync*'   , 'Join')    
    scheduler.util.editor.process(graphEdits, '*unblock*', 'UnBlock')    
    # add connections
    for processName in graph['processes']:
        # configure all processes so that they block
        blockCfg = { 'blocking' : { 'ReceivedAllInputs' : True } }
        scheduler.util.editor.setConfig(graph, processName, blockCfg)
        # send all process a Merge
        scheduler.util.editor.connection(graphEdits, (processName, 'events'), '*events*')
    scheduler.util.editor.connection(graphEdits, '*events*', '*sync*')
    scheduler.util.editor.connection(graphEdits, '*stdin*' , '*sync*')
    scheduler.util.editor.connection(graphEdits, '*sync*'  , '*unblock*')
    # add edits to given graph
    return scheduler.util.editor.combine(graph, graphEdits)
