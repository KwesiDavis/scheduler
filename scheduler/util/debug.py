'''
Synchronize user input with the start of a process
'''

import scheduler.util.editor

def add(graph):
    graphEdits = {}
    
    eventsPortName   = 'events'
    mergeProcessName = '*merge*'
    mergeInPortName  = 'in'
    for processName in graph['processes']:
        # Merge all process events
        conn = scheduler.util.editor.connection(graphEdits, (processName, 'events'), '*merge*')
        connections.append( conn )
    connections.append( scheduler.util.editor.connection(graphEdits, '*events*', '*sync*') )
    connections.append( scheduler.util.editor.connection(graphEdits, '*stdin*' , '*sync*') )
    connections.append( scheduler.util.editor.connection(graphEdits, '*sync*'  , '*unblock*') )

    graph.update(graphEdits) 
    return graph
