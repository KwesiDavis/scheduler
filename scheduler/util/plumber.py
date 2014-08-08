import logging, os
from multiprocessing import Pipe, Process
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
    
def start(workers, leak):
    '''
    Closing unused file descriptors held by threads, closes them in the parent 
    process also. The parent process passes a copy of its file descriptors to 
    its spawned child processes. So this method makes sure all Threads start 
    after all Processes, so processes don't inherit closed file descriptors.
    
    Parameters:
        workers - A list of workers (Process or Thread objects)
        leakyPipes - A list of Pipes created in the parent process; which have
                     leaked their file descriptors into child workers. 
    '''
    for worker in sorted(workers, cmp=compareWorkers):
        worker.start()
    # Handle un-used file descriptors held by the parent process.
    processName = '<none>'
    connInfos, sharing = leak
    closeByProcess(connInfos, processName, sharing=sharing)

def connectionInfo( conn, process, port, parent=None ):
    '''
    '''
    return { 'connection' : conn,
             'process'    : process,
             'port'       : port,
             'parent'     : parent }

def closeByProcess(connInfos, process, sharing=[]):
    if process in sharing:
        # Treat all aliases as one since they share the same process id
        processNames = sharing
    else:
        processNames = [ process ]
        
    pid = os.getpid()
    for connInfo in connInfos['inports'] + connInfos['outports']:
        logging.debug('{prefix}: [{pid}] On init, process "{proc}" opened "{pipeProc}.{pipePort}".'.format(prefix='LEAK', pid=pid, pipeProc=connInfo['process'], pipePort=connInfo['port'], proc=process))     
        if connInfo['process'] in processNames:
            continue
        logging.debug('LEAK: [{pid}] On init, process "{proc}" closed "{pipeProc}.{pipePort}".'.format(pid=pid, pipeProc=connInfo['process'], pipePort=connInfo['port'], proc=process))
        connInfo['connection'].close()
