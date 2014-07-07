import json, logging, sys, argparse
from multiprocessing import Process, Pipe, Queue, Event, Manager

def externalConnIter(graph, inports=True):
    '''
    Given a graph iterate over the connections that touch an external port.
    
    Parameters:
        graph - A graph of data relationships between the ports of components 
        inports - When 'True', the default, include connections that involve 
                  both in-ports and out-ports. Otherwise, ignore in-ports.
    Returns:
        Yields a tuple of the form: (srcProcessName, srcPortName, 
        tgtProcessName, tgtPortName, None)     
    '''
    type2direction = {'outports' : ('tgtProcessName', 'tgtPortName',  'srcProcessName', 'srcPortName')}
    if inports:
       type2direction.update({'inports' : ('srcProcessName', 'srcPortName', 'tgtProcessName', 'tgtPortName')})
    for portType, (mainProcessName, mainPortName, internalProcessName, internalPortName) in type2direction.items():
        retval = {}
        for externalPortName in graph[portType]:
            retval[mainProcessName]     = '_main_'
            retval[mainPortName]        = externalPortName
            retval[internalProcessName] = graph[portType][externalPortName]['process']
            retval[internalPortName]    = graph[portType][externalPortName]['port']
            yield retval['srcProcessName'], retval['srcPortName'], retval['tgtProcessName'], retval['tgtPortName'], None
    
def internalConnIter(graph, iips=True):
    '''
    Given a graph iterate over the connections that *do not* touch an external port.
    
    Parameters:
        graph - A graph of data relationships between the ports of components 
        iips - When 'True', the default, include connections represented as 
               IIPs embedded in the given graph. Otherwise, ignore these IIPs.   
    Returns:
        Yields a tuple of the form: (srcProcessName, srcPortName, 
        tgtProcessName, tgtPortName, data)     
    '''
    iipCount = 0
    for connection in graph['connections']:
        data = None
        try:
            srcProcessName = connection['src']['process']
            srcPortName    = connection['src']['port']
        except KeyError:
            if not iips: continue
            srcProcessName = '_main_'
            srcPortName    = '_%s_' % iipCount
            iipCount      += 1
            data           = connection['data']
        tgtProcessName = connection['tgt']['process']
        tgtPortName    = connection['tgt']['port']
        yield srcProcessName, srcPortName, tgtProcessName, tgtPortName, data

def graph2network(graph, library, asIs=True, eventQueue=None):
    '''
    Given a graph and a component library generate a sub-network of Python
    multiprocessing Process objects wired to together with Pipe objects.
    
    Parameters:
        graph - A graph of data relationships between the ports of components
        library - A dictionary mapping component names to a function object 
                  that represents the component's business logic.
        asIs - When 'True', the default, the IIPs embedded in the given graph
               trump any connections coming from in-ports.
        eventQueue - A running processes will post internal events to this queue. 
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
    iips   = []
    iters  = [externalConnIter(graph, inports=(not asIs)), internalConnIter(graph, iips=asIs)]
    for iter in iters:
        for srcProcessName, srcPortName, tgtProcessName, tgtPortName, data in iter:
            logging.debug('CONN: {srcProc}.{srcPort} -> {tgtProc}.{tgtPort}'.format(srcProc=srcProcessName,
                                                                                    srcPort=srcPortName,
                                                                                    tgtProc=tgtProcessName,
                                                                                    tgtPort=tgtPortName))            
            connSrc, connTgt = Pipe()
            srcPortNameStr = str(srcPortName) # unicode-to-str
            interfaces.setdefault(srcProcessName, {})[srcPortNameStr] = connSrc
            tgtPortNameStr = str(tgtPortName) # unicode-to-str
            interfaces.setdefault(tgtProcessName, {})[tgtPortNameStr] = connTgt
            if data:
                iips.append((connSrc, data, srcProcessName, srcPortName))
    # parse processes
    subProcesses = []
    for processName in graph['processes'].keys():
        # Every process gets a name
        interfaces[processName]['_name_'] = processName
        # Every process knows where to log internal events        
        if eventQueue:
            interfaces[processName]['_event_queue_'] = eventQueue
            interfaces[processName]['_block_']       = True
        # Generate a process instance from a component name
        logging.debug('PROC: {proc}'.format(proc=processName))
        fxn = library[graph['processes'][processName]['component']]
        subProcesses.append( Process(target=fxn, kwargs=interfaces[processName]) )
    return iips, subProcesses, interfaces

def startNetwork(processes):
    '''
    Startup the processes in the sub-network.
    
    Parameters:
        processes - A complete list of processes in the sub-network
    '''
    for process in processes:
        process.start()

def sendIIPs(iips):
    '''
    Stimulate sub-network with initial information packets (or IIPs).
    
    Parameters:
        iips - A list of tuples of the form: (connection, data)
    '''
    for conn, data, processName, portName in iips:
        logging.debug('IIP : {data} = {proc}.{port}'.format(data=str(data),
                                                            proc=processName,
                                                            port=portName))    
        conn.send(data)
        conn.close()
        
def printOutPorts(interface, outportNames):
    '''
    Display the results of the sub-network.
    
    Parameters:
        interface - A dictionary mapping the main process' external port names
                    to connections.
        outportNames - A list of out-ports to query results for 
    '''
    for portName, conn in interface.items():
        if portName in outportNames:
            # wait for results
            data = conn.recv()
            logging.debug('RECV: {data} = {proc}.{port}'.format(data=str(data),
                                                                proc='_main_',
                                                                port=portName))             
            logging.info("_main_.%s = %s" % (portName, data))
            conn.close()

def stopNetwork(processes):
    '''
    Shutdown the sub-network of processes.
    
    Parameters:
        processes - A complete list of processes in the sub-network
    '''
    for process in processes:
        # Wait of all children to terminate themselves so we can exit the main
        # process without leaving orphaned processes behind.    
        process.join()

def json2graph(path):
    '''
    Load the given JSON graph file.
    
    Parameters:
        path - A path to a JSON file.
    Returns:
        A dictionary representing a graph of data relationships between the 
        ports of components.
    '''
    f = open(path, "r")
    return json.loads(f.read())

def add(a=None, b=None, sum=None, **kwargs):
    '''
    Logic for a simple 'Add' component.
    
    Parameters:
        a - A connection to receive the left addend.
        b - A connection to receive the right addend.
        sum - A connection to send the result of a+b. 
        kwargs - Extra arguments that the component doesn't know about.       
    '''
    import logging
    name = kwargs['_name_']    
    logging.debug('BGIN: {name}'.format(name=name))
    # Receive inputs
    aData   = a.recv()
    logging.debug('RECV: {data} = {proc}.{port}'.format(data=str(aData),
                                                        proc=name,
                                                        port='a'))    
    bData   = b.recv()
    logging.debug('RECV: {data} = {proc}.{port}'.format(data=str(bData),
                                                              proc=name,
                                                              port='b'))
    # Log internal even
    isEventsEnabled = kwargs.has_key('_event_queue_')
    if isEventsEnabled:
        # Broadcast a message/event that this process has all its inputs.
        event   = {'sender'  : name,
                   'type'    : 'ReceivedAllInputs'}
        # Does this event have framework-blocking powers?
        # MAINT: Currently there is only one type of event 
        #        and it's the blocking kind. Need a way to
        #        configure this per event type.
        if kwargs['_block_']:
            event['blocker'] = Manager().Event()
            eventQueue.put(event)
            event['blocker'].wait()
        else:
            eventQueue.put(event)
    # Do the 'add' operation
    #sum.send(a.recv()+b.recv())
    sumData = aData+bData
    # Send the results to output(s)
    logging.debug('SEND: {data} = {proc}.{port}'.format(data=str(sumData),
                                                        proc=name,
                                                        port='sum'))    
    sum.send(sumData)
    # Close my connections    
    for conn in [a, b, sum]:
        conn.close()       
    if isEventsEnabled:    
        #debugConn.close()
        eventQueue.close()
    logging.debug('END : {name}'.format(name=name))

def synchronizer(eventQueue, maxEvents):
    ''' 
    Linearize the cluster of parallel processes by forcing them to wait for 
    user input before they run. Useful for debugging.
    
    Parameters:
        eventQueue - A queue of events from running processes.
        maxEvents - A maximum number of 'ReceivedAllInputs' events to unblocked.
    '''
    import sys
    eventCount = 0
    while eventCount < maxEvents:
        while not eventQueue.empty():
            event     = eventQueue.get()
            userInput = sys.stdin.readline()
            if event['type'] == 'ReceivedAllInputs':
                event['blocker'].set()
                eventCount += 1
    # cleanup
    eventQueue.close()

if __name__ == '__main__':
    # parse command-line args
    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('-log', type=str, help='Set the log level', default="WARN")
    parser.add_argument('-sync', help='Step over processes, one-by-one, with the "Enter" key.', action="store_true")    
    args = parser.parse_args(sys.argv[1:])
    # set the log level
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % numeric_level)
    logging.basicConfig(level=numeric_level)
    # Create queue to log events
    eventQueue = None
    if args.sync:
        eventQueue = Queue()
    # Create a library of supported components
    library = {'Add':add}  
    # Load a graph from disk
    path    = './graphs/add_tree.json'
    graph   = json2graph(path)
    # Build a network from the graph
    network = graph2network(graph, library, eventQueue=eventQueue)
    iips, subProcesses, interfaces = network
    # Run the network
    startNetwork(subProcesses)
    sendIIPs(iips)
    # Synchronize two events:
    #  1) a process getting all its inputs
    #  2) the user hitting 'Enter' the key
    if args.sync:
        synchronizer(eventQueue, len(graph['processes']))
    # Display the network's output
    printOutPorts(interfaces['_main_'], graph['outports'])
    # Tear down the network
    stopNetwork(subProcesses)
