import os, sys, select, logging  
import scheduler.network
import scheduler.component.base
import scheduler.util.editor

def add(core, inports, outports):
    '''
    Logic for a simple 'Add' component.
    
    Call the '+' operator on its pair of inputs. 
    
    Parameters:
        a - A connection to receive the left addend.
        b - A connection to receive the right addend.
        sum - A connection to send the result of a+b. 
    '''    
    def fxn(core):
        try:
            a = core['getData']('a')
            b = core['getData']('b')
        except EOFError:
            pass
        else:
            result = a+b
            try:
                core['setData']('sum', result)
            except IOError:
                pass # downstream connection is closed
    scheduler.component.base.fxn(core, inports, outports, fxn)

def stdin(core, inports, outports):
    '''
    Logic the simple 'StdIn' component.
    
    Reads standard in from the main process. Must run as thread of the main-process.
    http://repolinux.wordpress.com/2012/10/09/non-blocking-read-from-stdin-in-python/
    
    Parameters:
        out - Data on this port came from standard-in. 
    '''    
    def fxn(core):
        if sys.stdin.isatty():
            print "Hit 'Ctrl-D' to exit input stream:"
        DONT_BLOCK = 0
        while True:
            # When user hits the 'Enter' key, select() will append the 
            # standard-in file object to the first list in the resultant tuple.
            hasInput, _, _ = select.select([sys.stdin], [], [], DONT_BLOCK) 
            if hasInput:
                # There is input sitting on standard-in. Forward it to the
                # out-port.
                line = sys.stdin.readline()
                if line:
                    try:
                        core['setData']('out', line.replace('\n',''))
                    except IOError:
                        break # downstream connection is closed
                # The user hit 'Ctrl-D'; which means end-of-file.
                else:
                    break
    scheduler.component.base.fxn(core, inports, outports, fxn)
    
def stdout(core, inports, outports):
    '''
    Logic for the 'StdOut' component.
    
    Writes to standard-out from the main process. Must run as thread of the main-process.
    
    Parameters:
        in - Data on this port is sent to standard-out. 
    '''
    def fxn(core):
        DONT_BLOCK = 0        
        while True:
            _, outputReady, _ = select.select([], [sys.stdout], [], DONT_BLOCK)
            if outputReady:
                try:
                    line = core['getData']('in')
                except EOFError:
                    # Upstream connection closed so stop polling for lines
                    break
                sys.stdout.write(str(line)+'\n')
                sys.stdout.flush()
    scheduler.component.base.fxn(core, inports, outports, fxn)
    
def noop(core, inports, outports):
    '''
    Logic for the 'NoOp' component.
    
    All in-coming data is immediately sent out unmolested.
    
    Parameters:
        in - Anything data object.
        out - Everything data object, that arrived on the in-port, is forwarded
              to this out-port.
    '''
    def fxn(core):
        try:
            data = core['getData']('in')
        except EOFError:
            pass # upstream data source stopped
        else:
            try:
                core['setData']('out', data)
            except IOError:
                pass # downstream connection is closed
    scheduler.component.base.fxn(core, inports, outports, fxn)

def info(core, inports, outports):
    '''
    Logic for the 'Info' component.
    
    All in-coming data is immediately sent out unmolested.
    
    Parameters:
        in - Anything data object.
        out - Everything data object, that arrived on the in-port, is forwarded
              to this out-port.
    '''
    def fxn(core):
        while True:
            try: 
                data = core['getData']('in')
            except EOFError: 
                break # upstream data source stopped         
            logging.info(str(data))
            try:
                core['setData']('out', data)
            except IOError:
                break # downstream connection is closed
    scheduler.component.base.fxn(core, inports, outports, fxn)
    
def merge(core, inports, outports):
    '''
    Logic for the 'Merge' component.
    
    Listens to multiple connections on its single in-port and forwards all 
    input data to its single output on a first-in-first-out basis.   
    
    Parameters:
        in - Anything data object, from multiple source connections.
        out - Everything data object, that arrived on the multi-connected
              in-port, in the order it was received.
    '''
    def fxn(core):
        connIndices = range(core['lenAt']('in'))
        # Keep track of the status of every connection to this port
        eof = [False for connIndx in connIndices]
        while True:
            for connIndx in connIndices:
                if not eof[connIndx]:
                    try:
                        data = core['getDataAt'](connIndx, 'in', block=False)
                    except ValueError:                        
                        # no data on in-port
                        continue
                    except EOFError:
                        # no more data is coming                        
                        eof[connIndx] = True
                        continue
                    try:
                        core['setData']('out', data)
                    except IOError:
                        break # downstream connection is closed
            if all(eof):
                # All upstream connections are closed so stop polling 
                # for data
                break
    scheduler.component.base.fxn(core, inports, outports, fxn, wait=False)

def join(core, inports, outports):
    '''
    Logic for the 'Join' component.
    
    Listens to multiple connections on its single in-port and waits for data to
    arrive from each connected source. When all the connections have supplied 
    data, these data are grouped into a list and sent to the out-port and 
    process starts over again waiting for data from all connections.
    
    Parameters:
        in - Anything data object, from multiple source connections.
        out - A list of data packets; one from each of the in-coming 
              connections.
    '''
    def fxn(core):
        connIndices = range(core['lenAt']('in'))
        isEndOfFile = False
        while not isEndOfFile:
            group = []            
            for connIndx in connIndices:
                try:
                    data = core['getDataAt'](connIndx, 'in', block=True)
                    group.append(data)
                except EOFError:
                    # If we get an EOF from any input we're done.
                    isEndOfFile = True
                    break
            if not isEndOfFile:
                try:
                    core['setData']('out', tuple(group))
                except IOError:
                    break # downstream connection is closed
    scheduler.component.base.fxn(core, inports, outports, fxn)

def unblock(core, inports, outports):
    '''
    Logic for the 'UnBlock' component.
    
    Unblocks the given synchronized event pair. One of the events is assumed 
    to be an internal event that needs to be unblocked.
    
    Parameters:
        in - A pair of events for the form: [stdinString, internalEvent]
    '''
    def fxn(core):
        while True:
            # get input
            try:
                data = core['getData']('in')
            except EOFError:
                break
            # unblock Event contained in tuple            
            for elem in data:
                try:
                    elem['blocker'].set() # unblock this Event obj
                except KeyError:
                    # dict has not Event blocking object
                    pass
                except TypeError:
                    pass
    scheduler.component.base.fxn(core, inports, outports, fxn)    

def subnet(core, inports, outports):
    '''
    Creates a bridge between two independent networks by forwarding IPs to the
    right ports.
    '''
    def fxn(core):
        pid        = os.getpid() # for logging
        FIRST_CONN = 0           # only one connection on exported ports
        
        # All inputs are ready so create the sub-network
        # Note: We ignore any IIPs returned for the new network.
        config = core['getConfig']()
        graph  = scheduler.util.editor.json2graph(config['graph'])
        
        # These are the open file descriptors (or connections) associated with
        # the ports on this process' external interface.  When this process 
        # creates child processes for the sub-network, these open file 
        # descriptors are inherited by (or 'leaked' into) the child processes. 
        # The child processes will not use these file descriptors so they must
        # close their inherited copy.
        processName = core['name']
        leak        = scheduler.util.plumber.getLeakByProcess( core['leak'], processName )
        network     = scheduler.network.new(graph, parentProcessName=processName, iips=False, leak=leak)
        # Note: The network's exported interface is identical to this current 
        #       component's interface.  The named ports are the same, but this 
        #       component's in-ports are on the target end of its pipe while 
        #       the network's in-ports, are on the source end of its pipe.  A 
        #       similar relationship applies to the out-ports.  The component's 
        #       out-ports are source connections, but the network's out-ports
        #       are targets.  
        interface   = network['interface']
        scheduler.network.start(network)
        # Do EOF bookkeeping on all in-ports and out-ports
        ins  = 'externalInports'
        outs = 'internalOutports'
        eof  = {ins  : {}.fromkeys(interface['inports'].keys(),  False),
                outs : {}.fromkeys(interface['outports'].keys(), False)}
        ioError = {outs : {}.fromkeys(interface['outports'].keys(), False)}
        # Forward external data to the internal sub-net and forward internal
        # results to the external out-ports.
        while True:
            # Handle data sent to the sub-net via connections on its external
            # in-port interface.
            for inportName in interface['inports'].keys():
                # If this connection is open and there is data available 
                # get it. 
                if not eof[ins][inportName]:
                    # Get the source end of the pipe that is connected to the 
                    # corresponding internal in-port.
                    # exported in-ports are connected to one, and only one, internal in-port 
                    assert( len(interface['inports'][inportName]) == 1 ) 
                    conn = interface['inports'][inportName][FIRST_CONN]
                    try:
                        data = core['getData'](inportName, block=False)
                    except ValueError:
                        # no data on in-port
                        continue
                    except EOFError:
                        # no more data is coming
                        eof[ins][inportName] = True
                        # Since the external in-port is closed, let's close 
                        # the source end of the pipe the is connected to the
                        # corresponding internal in-port.
                        logging.debug('CONN: [{pid}] Process "{proc}" closed "{proc}.{port} [{index}]".'.format(pid=pid, 
                                                                                                                proc=network['name'], 
                                                                                                                port=inportName, 
                                                                                                                index=FIRST_CONN))        
                        conn.close()
                        continue
                    # Forward the data from the external in-port to internal
                    # in-port.
                    conn.send(data)
                    logging.debug('SEND: {proc}.{port} = {data} (internal)'.format(data=str(data),
                                                                                   proc=processName,
                                                                                   port=inportName))
            # Handle data exiting the sub-net via connections to out-ports on
            # internal sub-processes.
            for outportName in interface['outports'].keys():
                # If this connection is open and there is data available 
                # get it. 
                if not eof[outs][outportName]:                
                    # exported out-ports are connected to one, and only one, internal out-port 
                    assert(len(interface['outports'][outportName]) == 1) 
                    conn = interface['outports'][outportName][FIRST_CONN]
                    if not conn.poll():
                        # no data on out-port
                        continue
                    try:
                        data = conn.recv()
                        logging.debug('RECV: {proc}.{port} = {data} (internal)'.format(data=str(data),
                                                                                       proc=processName,
                                                                                       port=outportName))                        
                    except EOFError:
                        # no more data is coming
                        eof[outs][outportName] = True
                        # Since the internal out-port is closed, let's close 
                        # the target end of the pipe that is connected to the
                        # corresponding external out-port.                        
                        logging.debug('CONN: [{pid}] Process "{proc}" closed "{proc}.{port} [{index}]".'.format(pid=pid, 
                                                                                                                proc=network['name'], 
                                                                                                                port=outportName, 
                                                                                                                index=FIRST_CONN))        
                        conn.close()
                        continue
                if not ioError[outs][outportName]:         
                    # Forward the data, that arrived on the internal out-port,
                    # to the corresponding external out-port.
                    try:
                        core['setData'](outportName, data)
                    except IOError:
                        ioError[outs][outportName] = True
                        if all(ioError[outs].values()):
                            break # *all* out-ports, on the external interface, are closed
            if all(eof[ins].values()) and all(eof[outs].values()) :
                # All not data is traveling into or out of the sub-net, shut 
                # it down.
                break
        # We are done.
        scheduler.network.stop(network)    
    scheduler.component.base.fxn(core, inports, outports, fxn)

'''
A dictionary that maps component names to a function object. The function 
represents the component's business logic.
'''
library = { 'Merge'    : merge,
            'Join'     : join,
            'UnBlock'  : unblock,
            'SubNet'   : subnet,
            'Add'      : add,
            '_StdIn_'  : stdin,
            '_StdOut_' : stdout,
            'Info'     : info,
            'NoOp'     : noop,
            '_NoOp_'   : noop }