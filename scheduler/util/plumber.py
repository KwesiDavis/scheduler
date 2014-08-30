import logging, os
from multiprocessing import Process
from threading import Thread

'''
This module helps handle file descriptor leaks from the use of 
multiprocessing.Pipe objects. If a Pipe was created in a parent
process and then a child Process (or Thread) is created, the child
inherits the parents file descriptors. If a developer, later, wishes
to close one (or both) ends of the Pipe; which rely on their associated
file descriptors, the developer must remember to close the file descriptor
in the parent process as well as the child process.

A detailed discussion of the issue here:
    http://legacy.python.org/dev/peps/pep-0446/

Repro:
    from multiprocessing import Pipe, Process
    
    def f(srcConn):
      srcConn.send('Hello!')
      srcConn.close()
    
    srcConn, tgtConn = Pipe()
    proc =  Process(target=f, args=(srcConn,))
    proc.start()
    # srcConn.close() # Solution is an extra close() here.
    try:
        print tgtConn.recv()
        tgtConn.recv() # script will hang here and never EOF
    except EOFError:
        print "Source end is closed!" 
'''

def compareWorkers(a,b):
    '''
    A compare function used to sort workers such that all 
    multiprocessing.Process objects appear in a list before any
    multiprocessing.Thread objects.

    Parameters:
        a - A worker (Process or Thread object)   
        b - A worker (Process or Thread object)
        
    Returns:
        A negative, zero or positive number depending on whether the first argument
        is considered "smaller" than, equal to, or "larger" than the second argument.
        Process objs are "smaller" than Threads, so the sort first in a list.
    '''
    if   isinstance(a, Process) and isinstance(b, Thread):
        retval = -1
    elif isinstance(a, Thread) and isinstance(b, Process):
        retval =  1
    else:
        retval =  0
    return retval
    
def start(workers, leak, processName):
    '''
    Starts all workers, but also makes sure that all Process workers start 
    *before* any Thread workers.      
    Note: Child worker Threads and Processes inherit open connections (or file
          descriptors) from the main parent process at start-time.  This method 
          starts child Threads (and child Processes) from the main parent 
          thread.  After a Thread starts, it will close all connections not 
          used by itself (or any other sibling thread).  When a Thread closes a
          connection, it also closes it in all sibling Threads and in the main 
          parent thread.  Thus, any Thread that starts, will close all 
          connections (in the main parent thread) used by all Processes.  So,
          any Process that starts, after any Thread, will inherit closed 
          connections that it expects to be open for use.  This would be bad.
          
    Parameters:
        workers - A list of workers (Process or Thread objects)
        leak - A list of all connections (or file descriptors) in-use by the 
               network of processes.        
        processName - The parent (or composite) process responsible for managing 
                      its network sub-processes. 
    '''
    for worker in sorted(workers, cmp=compareWorkers):
        worker.start() # fork new process (or thread)
    # Closed un-used file descriptors held by the given process.
    # Note: start() gets called by thread that creates the network (or the main
    #       thread) so it must also close its connections after all processes
    #       have started due to inheriting behavior of the a forked process. 
    closeByProcess(leak, processName)

def connectionInfo(conn, process, port, parent=None):
    '''
    One end of a Pipe (or a Connection object) and metadata describing who is 
    using the connection object.
    Note: This metadata is needed to handle the Pipe file descriptor leak.
    
    Parameters:
        conn - a Connection object returned from Pipe()
        process - the process using the connection object 
        port - the port, on the given process, being connected to
        parent - the composite-process that contains the given process
    Returns:
        A dictionary representing one end of a Pipe. 
    '''
    return { 'connection' : conn,
             'process'    : process,
             'port'       : port,
             'parent'     : parent }

def closeByProcess(leak, processName):
    '''
    Close all connections (in the given list of leaked connections) that will
    not be used by the given process.
    Note: If the given process is a worker thread, the connections it "uses" 
          includes the connections being used by all other threads.   
     
    Parameters:
        leak - A list of all connections (or file descriptors) in-use by the 
               network of processes.
        processName - A process using connections on the network. 
    '''
    if processName in leak['threads']:
        # Treat all aliases as one since they share the same process id
        processNames = leak['threads']
    else:
        processNames = [ processName ]
        
    pid = os.getpid()
    for connInfo in leak['connections']['inports'] + leak['connections']['outports']:
        logging.debug('LEAK: [{pid}] On init, process "{proc}" opened "{pipeProc}.{pipePort}".'.format(pid=pid, pipeProc=connInfo['process'], pipePort=connInfo['port'], proc=processName))
        # MAINT: Take connInfo['parent'] into account     
        if connInfo['process'] in processNames:
            continue
        logging.debug('LEAK: [{pid}] On init, process "{proc}" closed "{pipeProc}.{pipePort}".'.format(pid=pid, pipeProc=connInfo['process'], pipePort=connInfo['port'], proc=processName))
        connInfo['connection'].close()

def newLeak(inports=[], outports=[], threads=set([])):
    '''
    Create an object that knows about all of the leaked Pipe connections and 
    the names of all the Thread processes.
    
    Parameters:
        inports - A list of in-port connections (and associated metadata)
                  in-use by a network of processes. 
        outports - A list of out-port connections (and associated metadata) 
                  in-use by a network of processes. 
        threads - the names of workers that share a PID
    Returns:
        A dictionary representing A list of all connections (and associated 
        metadata) in-use by a network of processes. one end of a Pipe. 
    '''
    # the default value is only created once so return copies of the 
    # incoming mutable objects  
    retval = { 'connections' : { 'inports'  : list(inports),
                                 'outports' : list(outports) },
               'threads'     : set(threads) } 
    return retval 

def getLeakByProcess(leak, processName):
    '''
    Create an object that knows about all of the leaked Pipe connections
    associated with a given process.
    Note: The subnet (or parent) knows about all leaked connections in the 
          network that it resides. This method is used, by subnets, to 
          determine which connections, from the parent's network, are leaked
          into the child processes it spawns.
    
    Parameters:
        leak - A list of all connections (or file descriptors) in-use by the 
               network of processes.
        processName -  A process using connections on the network. 
    Returns:
        A dictionary representing A list of all connections (and associated 
        metadata) in-use by a network of processes. one end of a Pipe. 
    '''    
    aliases = [ processName ]
    if processName in leak['threads']:
        aliases = list(leak['threads'])
    ins     = [ connInfo for connInfo in leak['connections']['inports']  if connInfo['process'] in aliases]
    outs    = [ connInfo for connInfo in leak['connections']['outports'] if connInfo['process'] in aliases]
    threads = set(aliases)
    return newLeak(inports=ins, outports=outs, threads=threads)

def append(leak, parentProcessName, connection, processName, portName, isThread, inport=True):
    '''
    Add a new leaked connection object (and associated metadata) to an existing 
    list of Pipe connections used by a network.
    
    Parameters:
        leak - An existing list of all connections (or file descriptors) 
               in-use by the network of processes.
        connection - A connection (or one end of a Pipe) 
        processName - The process, on the network, that will use the given 
                      connection.
        portName - The port, on the given process, that will use the given 
                   connection.
        isThread - Is 'True', when the given process shares its PID with some 
                   other worker in the network. Is 'False' otherwise.
        inport - Is 'True', when the given port is and in-port. Is 'False' 
                 otherwise. 
    '''    
    portType = {True:'inports', False:'outports'}
    # Get namespace for the given process 
    namespace = parentProcessName
    isRoot = parentProcessName == processName
    if isRoot:
        namespace = None
    # Keep a list of all in-ports and out-ports
    leak['connections'].setdefault(portType[inport], []).append( connectionInfo(connection, processName, portName, parent=namespace) )
    # Keep track of workers that share a PID (and thus share file descriptors)
    if isThread:
        leak['threads'].add(processName)