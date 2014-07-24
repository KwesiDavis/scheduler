import sys, select
import scheduler.component
import logging  

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
        a      = core['getData']('a')
        b      = core['getData']('b')
        result = a+b
        core['setData']('sum', result)    
    scheduler.component.base(core, inports, outports, fxn)

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
                    core['setData']('out', line.replace('\n',''))
                # The user hit 'Ctrl-D'; which means end-of-file.
                else:
                    break
    scheduler.component.base(core, inports, outports, fxn)
    
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
    scheduler.component.base(core, inports, outports, fxn)
    
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
        data = core['getData']('in')
        core['setData']('out', data)
    scheduler.component.base(core, inports, outports, fxn)

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
            try: data = core['getData']('in')
            except EOFError: break             
            logging.info(str(data))
            core['setData']('out', data)
    scheduler.component.base(core, inports, outports, fxn)
    
def iip(core, inports, outports):
    '''
    Logic for a special 'IIP' component.
    
    Reads its configuration data and send initial information packets (or IIPs)
    to out-ports named after target in-ports for the IIPs data.
    
    Parameters:
        config - IIP data of the form: {'iip':[(data1, process1, port1), 
                                               (data2, process2, port2),
                                               (dataN, processN, portN)]}
        <process>_<port> - A port named after a target in-port for IIP data.
    '''
    def fxn(core):
        config = core['getConfig']()
        for iip in config['iips']:
            data, processName, portName = iip
            portName = '{proc}_{port}'.format(proc=processName, port=portName)  
            core['setData'](portName, data)
    scheduler.component.base(core, inports, outports, fxn)

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
        eof = [False for connIndx in connIndices]
        while True:
            for connIndx in connIndices:
                if not eof[connIndx]:
                    try:
                        data = core['getDataAt'](connIndx, 'in', block=False)
                    except IOError:
                        continue
                    except EOFError:
                        eof[connIndx] = True
                        continue
                    core['setData']('out', data)
            if all(eof):
                # All upstream connections are closed so stop polling 
                # for data
                break
    scheduler.component.base(core, inports, outports, fxn)

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
                core['setData']('out', tuple(group))
    scheduler.component.base(core, inports, outports, fxn)

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
    scheduler.component.base(core, inports, outports, fxn)    

'''
A dictionary that maps component names to a function object. The function 
represents the component's business logic.
'''
library = { '_IIPs_'   : iip,
            'Merge'    : merge,
            'Join'     : join,
            'UnBlock'  : unblock,      
            'Add'      : add,
            '_StdIn_'  : stdin,
            '_StdOut_' : stdout,
            'Info'     : info,
            'NoOp'     : noop,
            '_NoOp_'   : noop }