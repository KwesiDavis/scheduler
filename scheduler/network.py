import logging
from multiprocessing import Process
from threading import Thread

import scheduler.component.test
import scheduler.util.plumber

def new(graph):
    '''
    Given a graph and a component library generate a sub-network of Python
    multiprocessing Process objects wired to together with Pipe objects.
    
    Parameters:
        graph - A graph of data relationships between the ports of components
        library - A dictionary mapping component names to a function object 
                  that represents the component's business logic.
    Returns:
        A tuple of the form: (iips, subProcesses, processInterfaces)     
    '''
    # A mapping of process names to dictionaries. The dict's describe the 
    # in-ports and out-ports of all processes in the network.
    # Ex. interfaces = { 'process1' : { 'in'  : connTgtForPortIn,
    #                                   'out' : connSrcForPortOut},
    #                    'process2' : { 'a'   : connTgtForPortA,
    #                                   'b'   : connTgtForPortB,
    #                                   'sum' : connSrcForPortSum} }
    interfaces = {}
    # parse connections
    leakyPipes = [] # Pipe() artifacts :(
    for connection in graph['connections'] :
        # get connection info
        try:
            srcProcessName   = connection['src']['process']
        except KeyError:
            continue # skip IIP's            
        srcPortName      = connection['src']['port']
        tgtProcessName   = connection['tgt']['process']
        tgtPortName      = connection['tgt']['port'] 
        # connect the source process to the target process
        isSrcThreaded    = scheduler.component.isThreaded(graph['processes'][srcProcessName]['component'])
        isTgtThreaded    = scheduler.component.isThreaded(graph['processes'][tgtProcessName]['component'])
        pipeTgt, pipeSrc = scheduler.util.plumber.pipePair(srcProcessName, srcPortName, isSrcThreaded,
                                                           tgtProcessName, tgtPortName, isTgtThreaded,
                                                           leakyPipes)
        logging.debug('PIPE: {srcProc}.{srcPort} -> {tgtProc}.{tgtPort}'.format(srcProc=srcProcessName,
                                                                                srcPort=srcPortName,
                                                                                tgtProc=tgtProcessName,
                                                                                tgtPort=tgtPortName))
        srcPortNameStr = str(srcPortName) # unicode-to-str
        interfaces.setdefault(srcProcessName, {}).setdefault('outports', {}).setdefault(srcPortNameStr, []).append(pipeSrc)
        tgtPortNameStr = str(tgtPortName) # unicode-to-str
        interfaces.setdefault(tgtProcessName, {}).setdefault('inports',  {}).setdefault(tgtPortNameStr, []).append(pipeTgt)
    # parse processes
    processes = []
    for processName in graph['processes'].keys():
        # Every process gets a name
        interfaces[processName].setdefault('core', {})['name'] = processName
        # Every keeps its metadata, if any
        interfaces[processName]['core']['metadata'] = graph['processes'][processName].get('metadata', {}) 
                
        interfaces[processName].setdefault('inports', {})
        interfaces[processName].setdefault('outports', {})
        # Generate a process instance from a component name
        logging.debug('PROC: {proc}'.format(proc=processName))
        componentName = graph['processes'][processName]['component']
        fxn = scheduler.component.test.library[componentName]
        if scheduler.component.isThreaded(componentName):
            processes.append( Thread(target=fxn, kwargs=interfaces[processName]) )
        else:
            processes.append( Process(target=fxn, kwargs=interfaces[processName]) )
    return (processes, leakyPipes)

def start(network):
    '''
    Startup the processes in the sub-network.
    
    Parameters:
        processes - A complete list of processes in the sub-network
    '''
    processes, leakyPipes = network
    scheduler.util.plumber.start(processes, leakyPipes)

def stop(network):
    '''
    Shutdown the sub-network of processes.
    
    Parameters:
        processes - A complete list of processes in the sub-network
    '''
    processes, _ = network
    for process in processes:
        # Wait of all children to terminate themselves so we can exit the main
        # process without leaving orphaned processes behind.    
        process.join()