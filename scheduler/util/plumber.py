import time, logging, os, sys
from multiprocessing import Pipe, Process
from threading import Thread

'''
'''

def leakyPipe(src, tgt, srcEnable=False, tgtEnable=False, sharing=False, leakyPipes=[],
              srcProcessName='<none>', srcPortName='<none>',
              tgtProcessName='<none>', tgtPortName='<none>'):
    '''
    For a particular process ID, this object represents a Pipe who's pair of 
    file descriptors were inherited (or have leaked) into another process.
    
    Parameters:
        src - A copy of a shared multiprocessing.Connection (or file 
              descriptor handle) for the source end of the leaky Pipe.
        tgt - A copy of a shared multiprocessing.Connection (or file 
              descriptor handle) for the target end of the leaky Pipe.
        srcEnable - When 'True' the source end of the Pipe is in-use for this 
                    particular process ID.
        tgtEnable - When 'True' the target end of the Pipe is in-use for this 
                    particular process ID.
        sharing - When 'True', the parallel worker (process or thread) that 
                  has the source end of the Pipe shares the same process ID as
                  the worker that has the target end.
        leakyPipes - A list of all the Pipes created by the parent process.
        srcProcessName - The name of the process that has the source end
                         of the Pipe.
        srcPortName - The name of the port that the Pipe's source end 
                      represents.
        tgtProcessName - The name of the process that has the target end
                         of the Pipe. 
        tgtPortName - The name of the port that the Pipe's target end 
                      represents.
                      
    Returns:
        A particular worker's copy of a pipe with file descriptors (or 
        Connection objects) that were inherited from a parent process.   
    '''
    return {'src'     : { 'conn'    : src, 
                          'enable'  : srcEnable,
                          'process' : srcProcessName,
                          'port'    : srcPortName },
            'tgt'     : { 'conn'    : tgt,
                          'enable'  : tgtEnable,
                          'process' : tgtProcessName,
                          'port'    : tgtPortName },
            'sharing' : sharing,
            'pid'     : os.getpid(),
            'leaks'   : leakyPipes} 

def pipePair(srcProcessName, srcPortName, isSrcThreaded,
             tgtProcessName, tgtPortName, isTgtThreaded,
             leaks):
    '''
    Create a pair of leaky pipes representing inherited copies of a Pipe 
    created in the parent process. The pipes correspond to pipes leaked to the
    worker holding the source end and the worker holding the target end of
    the pipe.  
    
    Parameters:
        srcProcessName - The name of the process that has the source end
                         of the Pipe.
        srcPortName - The name of the port that the Pipe's source end 
                      represents.
        isSrcThreaded - Set to 'True' when the worker holding the source end of
                        the pipe is a multiprocessing.Thread.
        tgtProcessName - The name of the process that has the target end
                         of the Pipe. 
        tgtPortName - The name of the port that the Pipe's target end 
                      represents.
        isTgtThreaded - Set to 'True' when the worker holding the target end of
                        the pipe is a multiprocessing.Thread.
        leaks - A list of objects representing all pipes (and their associated 
                worker names) leaked from the parent process.

    Returns:
        A tuple (leakyTargetPipe, leakySourcePipe) of leaky pipes representing 
        copies of the same pipe held by different workers.  
    '''    
    connTgt, connSrc = Pipe()
    isSharingPID     = isSrcThreaded and isTgtThreaded    
    
    srcName          ='{proc}.{port}'.format( proc=srcProcessName, port=srcPortName)
    tgtName          ='{proc}.{port}'.format( proc=tgtProcessName, port=tgtPortName)
    
    pipeParent       = leakyPipe(connSrc, connTgt, srcEnable=isSrcThreaded, tgtEnable=isTgtThreaded, sharing=isSharingPID, leakyPipes=[], srcProcessName=srcProcessName, srcPortName=srcPortName, tgtProcessName=tgtProcessName, tgtPortName=tgtPortName)
    pipeChildSrc     = leakyPipe(connSrc, connTgt, srcEnable=True,          tgtEnable=False,         sharing=isSharingPID, leakyPipes=leaks, srcProcessName=srcProcessName, srcPortName=srcPortName, tgtProcessName=tgtProcessName, tgtPortName=tgtPortName)
    pipeChildTgt     = leakyPipe(connSrc, connTgt, srcEnable=False,         tgtEnable=True,          sharing=isSharingPID, leakyPipes=leaks, srcProcessName=srcProcessName, srcPortName=srcPortName, tgtProcessName=tgtProcessName, tgtPortName=tgtPortName)
    
    leaks.append((pipeParent, (srcProcessName, tgtProcessName)))
    return pipeChildTgt, pipeChildSrc
        
def plugLeak(leakyPipe, processName, main=False):
    '''
    Close all inherited file descriptors (or ends of pipes) that we do not 
    intend to use for communication between this worker and its network 
    neighbors.
    
    Parameters:
        leakyPipe - A pair of leaked (or inherited) file descriptors associated
                    with a particular process ID (or worker).
        processName - The name of the worker holding the leaky pipe 
        main - When 'True' this is the parent process' copy of the leaky pipe.
    '''
    pid         = os.getpid()
    isThread    = (pid == leakyPipe['pid']) and not main
    prefix      = 'CONN' if main else 'LEAK'
    
    for connStr, _ in [ (connStr, leakyPipe[connStr]['conn']) for connStr in ['src', 'tgt']]:
        if not isThread:
            logging.debug('{prefix}: [{pid}] On init, process "{proc}" opened "{pipeProc}.{pipePort}".'.format(prefix=prefix, pid=pid, pipeProc=leakyPipe[connStr]['process'], pipePort=leakyPipe[connStr]['port'], proc=processName))     
    # close un-used ports
    if not leakyPipe['sharing']:
        for connStr, conn in [ (connStr, leakyPipe[connStr]['conn']) for connStr in ['src', 'tgt'] if not leakyPipe[connStr]['enable']]:
            if not isThread:
                # Pretend threads don't participate in initialize
                logging.debug('LEAK: [{pid}] On init, process "{proc}" closed "{pipeProc}.{pipePort}".'.format(prefix=prefix, pid=pid, pipeProc=leakyPipe[connStr]['process'], pipePort=leakyPipe[connStr]['port'], proc=processName))
            conn.close()
    if not isThread:
        for lp, workerNames in leakyPipe['leaks']:
            if processName not in workerNames:
                for connStr in ['src', 'tgt']:
                    lp[connStr]['conn'].close()
    
def getConnection(leakyPipe):
    '''
    For a given leaky pipe, get the associated multiprocessing.Connection
    object that is being used. 

    Parameters:
        leakyPipe - A pair of leaked (or inherited) file descriptors associated
                    with a particular process ID (or worker).
    '''
    srcEnable = leakyPipe['src']['enable']
    tgtEnable = leakyPipe['tgt']['enable']
    if srcEnable and not tgtEnable:
        return leakyPipe['src']['conn']
    elif tgtEnable and not srcEnable:
        return leakyPipe['tgt']['conn']
    else:
        return None
    
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
    
def start(workers, leakyPipes):
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
    for leakyPipe, _ in leakyPipes:
        plugLeak(leakyPipe, processName, main=True)