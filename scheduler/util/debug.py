'''
Synchronize user input with the start of a process
'''

import scheduler.util.editor

def add(graph):
    '''
    Adds a debug tool to the given graph. All internal messages are sent to a
    Merge node.  The output of the Merge is synchronized with the output of a
    StdIn node with a Join node. The output of the Join is fed to an UnBlock 
    node; which allows the user to lurch forward through execution of the graph
    by hitting the 'Enter'-key.   
    
    Parameters:
        graph - Debug nodes are added to the given graph
    Returns:
        The altered graph with the additional debug nodes wired up.
    '''
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
    scheduler.util.editor.modify(graph, graphEdits)
    return graph
