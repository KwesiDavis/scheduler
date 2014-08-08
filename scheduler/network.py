import logging, os
from multiprocessing import Process, Pipe
from threading import Thread
import scheduler.component.base
import scheduler.component.elementary.test
import scheduler.util.plumber

def new(graph):
    '''
    Given a graph and a component library generate a sub-network of Python
    multiprocessing Process objects wired to together with Pipe objects.
    
    Parameters:
        graph - A graph of components connected together by data ports
    Returns:
        A tuple of the form: (processes, leakyPipes)  This tuple represents
        a network.  The 'processes' object is a complete list of processes 
        in the network.  The 'leakyPipes' is a list of all the Pipes 
        created by the parent process.
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
    conns = {}
    threads = set(['<none>'])
    for connection in graph['connections'] :
        # get connection info
        try:
            srcProcessName   = connection['src']['process']
        except KeyError:
            continue # skip IIP's            
        srcPortName      = connection['src']['port']
        tgtProcessName   = connection['tgt']['process']
        tgtPortName      = connection['tgt']['port']
        logging.debug('PIPE: {srcProc}.{srcPort} -> {tgtProc}.{tgtPort}'.format(srcProc=srcProcessName,
                                                                                srcPort=srcPortName,
                                                                                tgtProc=tgtProcessName,
                                                                                tgtPort=tgtPortName))

        # Build the interface of a worker based on it connections
        tgtConn, srcConn = Pipe()
        srcPortNameStr = str(srcPortName) # unicode-to-str
        interfaces.setdefault(srcProcessName, {}).setdefault('outports', {}).setdefault(srcPortNameStr, []).append(srcConn)
        tgtPortNameStr = str(tgtPortName) # unicode-to-str
        interfaces.setdefault(tgtProcessName, {}).setdefault('inports',  {}).setdefault(tgtPortNameStr, []).append(tgtConn)

        # Keep a list of all in-ports and out-ports
        conns.setdefault('inports', []).append( scheduler.util.plumber.connectionInfo(tgtConn, tgtProcessName, tgtPortName, parent=None) )
        conns.setdefault('outports', []).append( scheduler.util.plumber.connectionInfo(srcConn, srcProcessName, srcPortName, parent=None) )
        # Keep track of workers that share a PID (and file descriptors) 
        isSrcThreaded = scheduler.component.base.isThreaded(graph['processes'][srcProcessName]['component'])
        if isSrcThreaded:
            threads.add(srcProcessName)
        isTgtThreaded = scheduler.component.base.isThreaded(graph['processes'][tgtProcessName]['component'])
        if isTgtThreaded:
            threads.add(tgtProcessName)
        
    # parse processes
    processes = []
    for processName in graph['processes'].keys():
        # Every process gets all the connections explicitly
        interfaces[processName].setdefault('core', {})['connInfos'] = conns
        # Every process knows the names of the threads that are using (or sharing) connections
        interfaces[processName].setdefault('core', {})['sharing'] = list(threads) 
        # Every process gets a name
        interfaces[processName].setdefault('core', {})['name'] = processName
        # Every keeps its metadata, if any
        interfaces[processName]['core']['metadata'] = graph['processes'][processName].get('metadata', {}) 
                
        interfaces[processName].setdefault('inports', {})
        interfaces[processName].setdefault('outports', {})
        # Generate a process instance from a component name
        logging.debug('PROC: {proc}'.format(proc=processName))
        componentName = graph['processes'][processName]['component']
        fxn = scheduler.component.elementary.test.library[componentName]
        if scheduler.component.base.isThreaded(componentName):
            processes.append( Thread(target=fxn, kwargs=interfaces[processName]) )
        else:
            processes.append( Process(target=fxn, kwargs=interfaces[processName]) )
    return (processes, (conns, list(threads)))

def start(network):
    '''
    Start all the processes in the network.
    
    Parameters:
        network - A tuple returned from new() representing a network of 
                  connected processes.
    '''
    (processes, leak) = network
    scheduler.util.plumber.start(processes, leak)

def stop(network):
    '''
    Block until all network process have terminated themselves. To be called
    before the main program exits so network processes aren't orphaned.
    
    Parameters:
        network - A tuple returned from new() representing a network of 
                  connected processes.
    '''
    processes, _ = network
    for process in processes:
        process.join()