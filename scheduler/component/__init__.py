import os, logging
from multiprocessing import Manager
import scheduler.util.plumber

def isThreaded(componentName):
    return componentName.startswith('_') and componentName.endswith('_') 

def closeConnections(core, inports, outports):
    # Close all connections
    for ports in [inports, outports, core.get('ports', {})]:
        for portName, smartPipe in ports.items():
            logging.debug('CONN: [{pid}] On exit, process "{proc}" closed "{proc}.{port}".'.format(pid=os.getpid(), proc=core['name'], port=portName))        
            conn = scheduler.util.plumber.getConnection(smartPipe)
            conn.close()

def internalEvent(core, eventType):
    eventSender = core['name']
    try:
        # Get the port dedicated to sending internal events.
        connEvents = core['getData']('events')
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
        if isEventBlocking:
            event['blocker'] = Manager().Event()
            connEvents.send(event)
            event['blocker'].wait()
        # Blocking in not enabled so just send the event.
        else:
            connEvents.send(event)
    # Blocking on events is not enabled.
    except KeyError:
        pass
    
def base(core, inports, outports, fxn, config={}):
    # Close un-used end of Pipe connection
    for ports in [inports, outports, core.get('ports', {})]:
        for portName, leakyPipe in ports.items():
            scheduler.util.plumber.plugLeak(leakyPipe, core['name'])
            
    # Log that this component has started
    logging.debug('BGIN: {name}'.format(name=core['name']))
    # Create helper functions
    received = set([])
    def checkInputs():
        if received == set(inports.keys()):
            internalEvent(core, 'ReceivedAllInputs')
    def getDataFxn(inportName):
        try:
            leakyPipe = inports[inportName]
        except KeyError, e:
            # Trying to get data to an unconnected in-port
            logging.info('Data requested from an unconnected port: {proc}.{port}'.format(proc=core['name'],
                                                                                         port=inportName))
            raise e
        conn = scheduler.util.plumber.getConnection(leakyPipe)
        data = conn.recv()
        logging.debug('RECV: {proc}.{port} = {data}'.format(data=str(data),
                                                            proc=core['name'],
                                                            port=inportName))
        received.add(inportName)
        checkInputs()
        return data
    def setDataFxn(outportName, data):
        logging.debug('SEND: {proc}.{port} = {data}'.format(data=str(data),
                                                            proc=core['name'],
                                                            port=outportName))
        try:
            leakyPipe = outports[outportName]
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
    core['getData']   = getDataFxn
    core['setData']   = setDataFxn
    core['getConfig'] = getConfigFxn
    # Component may have no in-ports so check may succeed
    checkInputs()
    # Run the component logic
    fxn(core)
    # A process "closes" when all its inputs close
    isAllInputsClosed = False
    logging.debug('Waiting on {name}\'s in-ports ({inports}) to close...'.format(name=core['name'], inports=inports.keys()))
    while not isAllInputsClosed:
        status = []
        for portName in inports.keys():
            try:
                core['getData'](portName)
                status.append(False)
            except EOFError:
                status.append(True)
        isAllInputsClosed = all(status)
    logging.debug('Process {name} is shutting down.'.format(name=core['name']))
    # Close all connections
    for ports in [inports, outports, core.get('ports', {})]:
        for portName, smartPipe in ports.items():
            logging.debug('CONN: [{pid}] On exit, process "{proc}" closed "{proc}.{port}".'.format(pid=os.getpid(), proc=core['name'], port=portName))        
            conn = scheduler.util.plumber.getConnection(smartPipe)
            conn.close()
    # Log that this component has finished       
    logging.debug('END : {name}'.format(name=core['name']))