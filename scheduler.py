import json
from multiprocessing import Process, Pipe

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
            retval[mainProcessName]     = '__main__'
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
            srcProcessName = '__main__'
            srcPortName    = '__%s__' % iipCount
            iipCount      += 1
            data           = connection['data']
        tgtProcessName = connection['tgt']['process']
        tgtPortName    = connection['tgt']['port']
        yield srcProcessName, srcPortName, tgtProcessName, tgtPortName, data

def graph2network(graph, library, asIs=True):
    '''
    Given a graph and a component library generate a sub-network of Python
    multiprocessing Process objects wired to together with by Pipe objects.
    
    Parameters:
        graph - A graph of data relationships between the ports of components
        library - A dictionary mapping component names to a function object 
                  that represents the component's business logic.
        asIs - When 'True', the default, the IIPs embedded in the given graph
               trump any connections coming from in-ports.   
    Returns:
        A tuple of the form: (iips, mainProcesInterface, subProcesses)     
    '''
    # parse connections
    iips   = []
    kwargs = {}
    for iter in [externalConnIter(graph, inports=(not asIs)), internalConnIter(graph, iips=asIs)]:
        for srcProcessName, srcPortName, tgtProcessName, tgtPortName, data in iter:
            connSrc, connTgt = Pipe()         
            srcPortNameStr = str(srcPortName) # unicode-to-str
            kwargs.setdefault(srcProcessName, {})[srcPortNameStr] = connSrc
            tgtPortNameStr = str(tgtPortName) # unicode-to-str
            kwargs.setdefault(tgtProcessName, {})[tgtPortNameStr] = connTgt
            if data:
                iips.append((connSrc, data))
    # parse processes
    subProcesses = []
    for processName in graph['processes'].keys():
        fxn = library[graph['processes'][processName]['component']]
        subProcesses.append( Process(target=fxn, kwargs=kwargs[processName]) )
    return iips, kwargs['__main__'], subProcesses
            
def startNetwork(processes):
    '''
    Run the sub-network of process.
    
    Parameters:
        processes - A complete list of processes in the sub-network
    '''
    for process in processes:
        process.start()

def runNetwork(iips):
    '''
    Stimulate sub-network with initial information packets (or IIPs).
    
    Parameters:
        iips - A list of tuples of the form: (connection, data)
    '''
    for conn, data in iips:
        conn.send(data)
        conn.close()
        
def printOutPorts(interface, outportNames):
    '''
    Display the results of sub-network.
    
    Parameters:
        interface - A dictionary mapping external port names to connections.
        outportNames - 
    '''
    for portName, conn in interface.items():
        if portName in outportNames:
            # wait for results
            print "__main__.%s = %s" % (portName, conn.recv())
            conn.close()

def stopNetwork(processes):
    '''
    Shutdown the sub-network of process.
    
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
        A dictionary representing graph of data relationships between the 
        ports of components.
    '''
    f = open(path, "r")
    return json.loads(f.read())

def add(a=None, b=None, sum=None):
    '''
    Logic for a simple 'Add' component.
    
    Parameters:
        a - A connection to receive the left addend.
        b - A connection to receive the right addend.
        sum - A connection to send the result of a+b.        
    '''
    sum.send(a.recv()+b.recv())
    for conn in [a, b, sum]:
        conn.close()

if __name__ == '__main__':
    # Create a library of supported components
    library = {'Add':add}  
    # Load a graph from disk
    path    = './graphs/add_tree.json'
    graph   = json2graph(path)
    # Build a network from the graph
    network = graph2network(graph, library)
    iips, interface, processes = network
    # Run the network
    startNetwork(processes)
    runNetwork(iips)
    # Display the network's output
    printOutPorts(interface, graph['outports'])
    # Tear down the network
    stopNetwork(processes)
