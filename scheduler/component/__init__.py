import os, logging
from multiprocessing import Manager
import scheduler.util.plumber

def isThreaded(componentName):
    return componentName.startswith('_') and componentName.endswith('_') 

def internalEvent(core, eventType):
    eventSender = core['name']
    # Construct an event (or notification message).
    event  = {'sender' : eventSender,
              'type'   : eventType}
    # Does this event have framework-blocking powers?
    try:
        isEventBlocking = core['block_cfg'][eventType]
    # Blocking on this particular event is not defined so don't block.
    except KeyError:
        isEventBlocking = False
    # If blocking enabled attach an object to the out going message the
    # allows a recipient to unblock this process. 
    try:
        if isEventBlocking:
            event['blocker'] = Manager().Event()
            core['setData']('events', event)
            event['blocker'].wait()
        # Blocking in not enabled so just send the event.
        else:
            core['setData']('events', event)
    except KeyError, e:
        # Sending events is not enabled.
        logging.info('%s %s' % (eventSender, str(e)))
        return
    
def base(core, inports, outports, fxn, config={}):
    FIRST_CONN = 0
    state      = {}
    # round robin support
    state['set data count'] = {}
    for portName in outports.keys():
        state['set data count'][portName] = [ 0, len(outports[portName]) ]
    # event support
    state['has all inputs'] = False
    
    # Close un-used end of Pipe connection
    for ports in [inports, outports, core.get('ports', {})]:
        for portName, leakyPipeList in ports.items():
            for leakyPipe in leakyPipeList:
                scheduler.util.plumber.plugLeak(leakyPipe, core['name'])
            
    # Log that this component has started
    logging.debug('BGIN: {name}'.format(name=core['name']))
    # Create helper functions
    received = set([])
    def checkInputs():
        if not state['has all inputs'] and received == set(inports.keys()):
            internalEvent(core, 'ReceivedAllInputs')
            state['has all inputs'] = True
    def lenAtFxn(portName, inport=True):
        if inport:
            return len(inports[portName])
        return len(outports[portName])
    def getDataAtFxn(i, inportName, poll=False):
        try:
            leakyPipe = inports[inportName][i]
        except KeyError, e:
            # Trying to get data to an unconnected in-port
            logging.info('Data requested from an unconnected port: {proc}.{port}'.format(proc=core['name'],
                                                                                         port=inportName))
            raise e
        conn = scheduler.util.plumber.getConnection(leakyPipe)
        if poll:
            if not conn.poll():
                raise IOError('In-port {proc}.{port} not ready for recv()'.format(proc=core['name'],
                                                                                  port=inportName))
        data = conn.recv()
        logging.debug('RECV: {proc}.{port} = {data}'.format(data=str(data),
                                                            proc=core['name'],
                                                            port=inportName))
        received.add(inportName)
        checkInputs()
        return data
    def getDataFxn(inportName):
        connCount = len(inports[inportName])
        if connCount > 1:
            logging.info('In-port {proc}.{port} has {count} connections, but only one requested.'.format(proc=core['name'],
                                                                                                         port=inportName,
                                                                                                         count=connCount))
        return getDataAtFxn(FIRST_CONN, inportName)
    def setDataFxn(outportName, data):
        logging.debug('SEND: {proc}.{port} = {data}'.format(data=str(data),
                                                            proc=core['name'],
                                                            port=outportName))
        try:
            # Load ballence across out connection (per port) 
            numSetCalls, numConnections = state['set data count'][outportName]
            roundRobinIndex = numSetCalls % numConnections  
            leakyPipe = outports[outportName][roundRobinIndex]
            state['set data count'][outportName][0] += 1
        except KeyError:
            # Trying to send data to an unconnected out-port
            logging.info('Data ({data}) sent to unconnected port: {proc}.{port}'.format(data=str(data),
                                                                                        proc=core['name'],
                                                                                        port=outportName))
            return
        conn = scheduler.util.plumber.getConnection(leakyPipe)
        conn.send(data)
    def getConfigFxn():
        return config    
    core['getDataAt'] = getDataAtFxn
    core['getData']   = getDataFxn
    core['setData']   = setDataFxn
    core['getConfig'] = getConfigFxn
    core['lenAt']     = lenAtFxn
    # Component may have no in-ports so check may succeed
    checkInputs()
    # Run the component logic
    fxn(core)
    # A process "closes" when all its inputs close
    isAllInputsClosed = False
    logging.debug('WAIT: Waiting on {name}\'s in-ports {inports} to close...'.format(name=core['name'], inports=inports.keys()))
    while not isAllInputsClosed:
        status = []
        for portName, leakyPipeList in inports.items():
            for i, leakyPipe in enumerate(leakyPipeList):
                try:
                    core['getDataAt'](i, portName)
                    status.append(False)
                except EOFError:
                    status.append(True)
        isAllInputsClosed = all(status)
    logging.debug('WAIT: Done waiting! Process {name} is shutting down.'.format(name=core['name']))
    # Close all connections
    for ports in [inports, outports, core.get('ports', {})]:
        for portName, leakyPipeList in ports.items():
            for leakyPipe in leakyPipeList:
                logging.debug('CONN: [{pid}] On exit, process "{proc}" closed "{proc}.{port}".'.format(pid=os.getpid(), proc=core['name'], port=portName))        
                conn = scheduler.util.plumber.getConnection(leakyPipe)
                conn.close()
    # Log that this component has finished       
    logging.debug('END : {name}'.format(name=core['name']))