import sys, select
import scheduler.component
import logging  

def add(core, inports, outports):
    def fxn(core):
        '''
        Logic for a simple 'Add' component.
        
        Call the '+' operator on its pair of inputs. 
        
        Parameters:
            a - A connection to receive the left addend.
            b - A connection to receive the right addend.
            sum - A connection to send the result of a+b. 
        '''
        a   = core['getData']('a')
        b   = core['getData']('b')
        sum = a+b
        core['setData']('sum', sum)    
    scheduler.component.base(core, inports, outports, fxn)

def stdin(core, inports, outports):
    def fxn(core):
        '''
        Logic for a simple 'StdIn' component.
        
        Reads standard in from the main process. Must run as thread of the main-process.
        
        Parameters:
            out - Standard in. 
        '''
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
    def fxn(core):
        data = core['getData']('in')
        core['setData']('out', data)
    scheduler.component.base(core, inports, outports, fxn)

def info(core, inports, outports):
    def fxn(core):
        while True:
            try: data = core['getData']('in')
            except EOFError: break             
            logging.info(str(data))
            core['setData']('out', data)
    scheduler.component.base(core, inports, outports, fxn)

def main(core, inports, outports, config):
    def fxn(core):
        config = core['getConfig']()
        for iip in config:
            data, processName, portName = iip
            portName = '{proc}.{port}'.format(proc=processName, port=portName)  
            core['setData'](portName, data)
    scheduler.component.base(core, inports, outports, fxn, config=config)

def filter(core, inports, outports, config):
    def fxn(core):
        messageType = core['getConfig']()
        event = core['getData']('in')
        if event['type'] == messageType:
             core['setData']('out', event)
    scheduler.component.base(core, inports, outports, fxn, config=config)
    
def iip(core, inports, outports, config):
    def fxn(core):
        config = core['getConfig']()
        for iip in config:
            data, processName, portName = iip
            portName = '{proc}_{port}'.format(proc=processName, port=portName)  
            core['setData'](portName, data)
    scheduler.component.base(core, inports, outports, fxn, config=config)

def merge(core, inports, outports):
    def fxn(core):
        connIndices = range(core['lenAt']('in'))
        eof = [False for connIndx in connIndices]
        while True:
            for connIndx in connIndices:
                if not eof[connIndx]:
                    try:
                        data = core['getDataAt'](connIndx, 'in', poll=True)
                    except IOError, e:
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

library = { '_IIPs_'   : iip,
            'Merge'    : merge,
            'Add'      : add,
            '_StdIn_'  : stdin,
            '_StdOut_' : stdout,
            'Info'     : info,
            'NoOp'     : noop,
            '_NoOp_'   : noop,
            '_Main_'   : main,
            'Main'     : main }