import logging, os
from multiprocessing import Process, Pipe
from threading import Thread
import scheduler.component.base
import scheduler.component.elementary.test
import scheduler.util.plumber

def connectionIter(graph, iips=True):
    '''
    Iterate over both IIP and regular connections in the given graph and always
    yield a source, target and data field.  For IIPs, the source is a non-existent
    process called '_iips_' and the port is an integer (representing the IIP's
    order-of-appearance, in the given graph's connection list).  For regular
    connections, the data is None.
    
    Parameters:
        graph - A graph of components connected together by data ports
        iips - When 'True', the default, if there are IIPs in the given graph,
               yield connections for them; otherwise ignore (or skip) IIPs.
    Returns:
        A tuple representing a pipe between two processes, and the initial 
        data, if any, that should pass between them. The tuple is of the 
        form (srcInfo, tgtInfo, dataInfo) where:
        * srcInfo  == (srcProcessName, srcPortName)
        * tgtInfo  == (tgtProcessName, tgtPortName)
        * dataInfo == (isDataUsed,     data)
        Note: The data can be 'None' so 'isDataUsed' determines whether the 
              data should be stuffed into the pipe as an IIP.
    '''
    for i, connection in enumerate(graph['connections']):
        # Get connection info
        try:
            srcInfo  = (connection['src']['process'], connection['src']['port'])
            dataInfo = (False, None)
        # Handle IIPs   
        except KeyError:
            if not iips:
                # Ignore IIPs
                continue
            srcInfo  = ('_iips_', i)
            dataInfo = (True, connection['data'])
        tgtInfo = (connection['tgt']['process'], connection['tgt']['port'])
        yield srcInfo, tgtInfo, dataInfo

def exportIter(graph, parentProcessName):
    '''
    Iterate over both exported in-ports and exported out-ports in the given 
    graph and always yield a source, target and data field.  For in-ports, the
    source process is the given parent process.  For out-ports, the target 
    process is the given parent process.
    
    Parameters:
        graph - A graph of components connected together by data ports
        parentProcessName - The name of the composite component that contains 
                            the given graph (or 'root' for a top-level network).
    Returns:
        A tuple representing a pipe between two processes, and the initial 
        data, if any, that should pass between them. The tuple is of the 
        form (srcInfo, tgtInfo, dataInfo) where:
        * srcInfo  == (srcProcessName, srcPortName)
        * tgtInfo  == (tgtProcessName, tgtPortName)
        * dataInfo == (isDataUsed,     data)
        Note: The 'data' value is always 'None'.
    '''    # Define top-level interface
    for exportType in ['inports', 'outports']:
        for exportItem in graph[exportType].items():
            # Collect the connection data as a list of source & target tuples. The
            # tuples are  of the form: (process, port)
            externalPort, internalInfo = exportItem
            srcIdx,       tgtIdx       = 0, 1
            processIdx,   portIdx      = 0, 1
            connData = [ (parentProcessName, externalPort), (internalInfo['process'], internalInfo['port']) ]
            # For out-ports, reverse how the connection data is interpreted such 
            # that the network container process (or parent) is now the target 
            # (instead of the source) of the exported interface connection.
            if exportType == 'outports':
                connData.reverse()
                
            srcInfo  = (connData[srcIdx][processIdx], connData[srcIdx][portIdx])
            tgtInfo  = (connData[tgtIdx][processIdx], connData[tgtIdx][portIdx])
            dataInfo = (False, None)   
            yield srcInfo, tgtInfo, dataInfo

def new(graph, parentProcessName='root', iips=True, leak=None):
    '''
    Given a graph and a component library generate a sub-network of Python
    multiprocessing Process objects wired to together with Pipe objects.
    
    Parameters:
        graph - A graph of components connected together by data ports
        parentProcessName - The name of the composite component that contains 
                            the given graph (or 'root' for a top-level network).
                            Note: Every network is assumed to exist inside of 
                                  some other container process. This is the 
                                  name of this sub-network's container. All 
                                  exported ports, in the given graph, are 
                                  connected to this container.
        iips - When 'True', the default, extract IIP data from the given graph
               and stuff these data into the appropriate pipes on start-up.
        leak - A list of connections (or file descriptors) that are already 
               open for this PID.
    Returns:
        A dict representing the processes and connections of the given graph.
        The dict is of the form: 
          { 'name'      : parentProcessName,
            'processes' : listOfProcesses,
            'interface' : exportedInterface,
            'leak'      : leakedFileDescriptors }
    '''
    logging.debug("NET : %s" % parentProcessName )
    # Not using default kwarg for 'leak'. Only *one* object will be created
    # and Python will try to share it with other calls of this function.
    if None == leak:
        leak = scheduler.util.plumber.newLeak()        
    # Connections associated with this network's exported ports will 
    # reference this entire network, by name, (as if it were an elementary 
    # process). We add the main thread name here to prevent the main thread
    # from closing connections used by the these exported ports.
    # Note: The main process is not in the given graph's list of processes
    #       to run. It is a conceptual-process representing the entire network.
    leak['threads'].add(parentProcessName)
    # A mapping of process names to dictionaries. The dict's describe the 
    # in-ports and out-ports of all processes in the network.
    # Ex. interfaces = { 'process1' : { 'in'  : connTgtForPortIn,
    #                                   'out' : connSrcForPortOut},
    #                    'process2' : { 'a'   : connTgtForPortA,
    #                                   'b'   : connTgtForPortB,
    #                                   'sum' : connSrcForPortSum} }
    interfaces = {parentProcessName:{'inports':{}, 'outports':{}}}
    # parse connections (and build interfaces based on these connections)
    for pipeIter in [connectionIter(graph, iips=iips), exportIter(graph, parentProcessName)]:
        for pipe in pipeIter:
            tgtConn, srcConn = Pipe()
            
            srcInfo, tgtInfo, dataInfo  = pipe
            srcProcessName, srcPortName = srcInfo
            tgtProcessName, tgtPortName = tgtInfo
            isSendingData,  data        = dataInfo
            logging.debug('PIPE: {srcProc}.{srcPort} -> {tgtProc}.{tgtPort}'.format(srcProc=srcProcessName,
                                                                                    srcPort=srcPortName,
                                                                                    tgtProc=tgtProcessName,
                                                                                    tgtPort=tgtPortName))
            # Build the interface of a worker based on its connections
            srcPortNameStr = str(srcPortName) # unicode-to-str
            scrPortType    = 'outports' if srcProcessName != parentProcessName else 'inports' # exported in-ports connect to internal in-ports
            interfaces.setdefault(srcProcessName, {}).setdefault(scrPortType, {}).setdefault(srcPortNameStr, []).append(srcConn)
            tgtPortNameStr = str(tgtPortName) # unicode-to-str
            tgtPortType    = 'inports' if tgtProcessName != parentProcessName else 'outports' # exported out-ports connect to internal out-ports
            interfaces.setdefault(tgtProcessName, {}).setdefault(tgtPortType,  {}).setdefault(tgtPortNameStr, []).append(tgtConn)
            # Deliver IIP
            if isSendingData:
                srcConn.send(data)
                logging.debug('SEND: {proc}.{port} = {data}'.format(data=str(data),
                                                                    proc=srcProcessName,
                                                                    port=srcPortName))
            # Keep track of all open connections (or leaks)
            # Note: All connections will be inherited by spawned child processes
            #       (or threads).  These leaked connections should be closed, by 
            #       the child, if they are inherited as open.
            tgtIsThread = scheduler.component.base.isThreaded(graph, tgtProcessName)
            scheduler.util.plumber.append(leak, parentProcessName, tgtConn, tgtProcessName, tgtPortName, tgtIsThread, inport=True)
            srcIsThread = scheduler.component.base.isThreaded(graph, srcProcessName)
            scheduler.util.plumber.append(leak, parentProcessName, srcConn, srcProcessName, srcPortName, srcIsThread, inport=False)
    # parse processes
    processes = []
    for processName in graph['processes'].keys():
        # Every process has a complete interface (even if it has no connections)         
        interfaces[processName].setdefault('inports',  {})
        interfaces[processName].setdefault('outports', {})        
        interfaces[processName].setdefault('core',     {})
        # Every process gets some core attributes: name, metadata, inherited (or leaked) connections
        interfaces[processName]['core']['name']     = processName
        interfaces[processName]['core']['metadata'] = graph['processes'][processName].get('metadata', {}) 
        interfaces[processName]['core']['leak']     = leak
        # Generate a process instance from a component name
        componentName = graph['processes'][processName]['component']
        fxn           = scheduler.component.elementary.test.library[componentName]
        if scheduler.component.base.isThreaded(graph, processName):
            processes.append( Thread(target=fxn, kwargs=interfaces[processName]) )
        else:
            processes.append( Process(target=fxn, kwargs=interfaces[processName]) )
        logging.debug('PROC: {proc} ({comp})'.format(proc=processName, comp=componentName))
    return { 'name'      : parentProcessName,
             'processes' : processes,
             'interface' : interfaces[parentProcessName],
             'leak'      : leak }

def start(network):
    '''
    Start all the processes in the network.
    
    Parameters:
        network - A dict returned from new() representing a network of 
                  connected processes.
    '''
    scheduler.util.plumber.start(network['processes'], network['leak'], network['name'])

def stop(network):
    '''
    Block until all network process have terminated themselves. To be called
    before the main program exits so network processes aren't orphaned.
    
    Parameters:
        network - A dict returned from new() representing a network of 
                  connected processes.
    '''
    # Since no more data will be coming into the graph, close the most upstream
    # connections of the graph.
    isInport = True # close in-ports
    closePortsByType(network, isInport=isInport)
    # Wait for all processes to terminate themselves.
    for process in network['processes']:
        process.join()
    # Since all network processes have terminated (or joined), no more data will
    # be coming out of the graph.  We can close the most downstream connections 
    # of the graph.
    isInport = False # close out-ports
    closePortsByType(network, isInport=isInport)
        
def closePortsByType(network, isInport=True):
    '''
    Close all in-port (or out-port)connections on this network's exported
    interface.
    Note: The connections associated with the ports on the network's exported 
          interface are open, by default, such that the caller can send data to
          the network.  These connections must be closed when the caller has 
          finished sending data to the network.
    
    Parameters:
        network - A dict returned from new() representing a network of 
                  connected processes.
        inports - When 'True', all in-ports are closed.  When 'False', 
                  out-ports are closed.
    '''
    bool2type = { True  : 'inports',
                  False : 'outports' }
    for inportName, conns in network['interface'][bool2type[isInport]].items():
        for i, conn in enumerate(conns):
            if not conn.closed:
                logging.debug('CONN: [{pid}] Process "{proc}" closed "{proc}.{port} [{index}]".'.format(pid=os.getpid(), proc=network['name'], port=inportName, index=i))        
                conn.close()
