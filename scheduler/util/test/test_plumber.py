import scheduler.util.plumber
import scheduler.util.editor
import scheduler.network
import unittest
from multiprocessing import Process, Pipe
from threading import Thread
import sys

class TestPlumber(unittest.TestCase):
    
    def setUp(self):
        self.graph = scheduler.util.editor.newGraph()
        self.count = 0
    
    def getNames(self, comp, count):
        components    = ['NoOp', '_NoOp_']
        processName   = components[comp].lower() + str(count)
        componentName = components[comp]
        return processName, componentName
    
    def runTwoNodes(self):
        for x in range(2):
            for y in range(2):
                # Create graph
                # -- pick components and name the processes
                self.count += 1
                processName1, componentName1 = self.getNames(x, self.count)
                self.count += 1
                processName2, componentName2 = self.getNames(y, self.count)
                # -- add components
                scheduler.util.editor.process(self.graph, processName1, componentName1)
                scheduler.util.editor.process(self.graph, processName2, componentName2)
                # -- add wire up the components
                scheduler.util.editor.connection(self.graph, processName1, processName2)
                # -- IIPs
                scheduler.util.editor.iip(self.graph, 'kick', processName1)
                # Run the graph
                network = scheduler.network.new(self.graph)
                scheduler.network.start(network)
                scheduler.network.stop(network)
    
    def test_TwoNodes(self):
        proc = Process(target=self.runTwoNodes)
        proc.start()
        proc.join()   
        self.assertEqual(0, proc.exitcode)
    
    def runThreeNodes(self):        
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    # Create graph
                    # -- pick components and name the processes
                    self.count += 1
                    processName1, componentName1 = self.getNames(x, self.count)
                    self.count += 1
                    processName2, componentName2 = self.getNames(y, self.count)
                    self.count += 1
                    processName3, componentName3 = self.getNames(z, self.count)
                    # -- add components
                    scheduler.util.editor.process(self.graph, processName1, componentName1)
                    scheduler.util.editor.process(self.graph, processName2, componentName2)
                    scheduler.util.editor.process(self.graph, processName3, componentName3)
                    # -- add wire up the components
                    scheduler.util.editor.connection(self.graph, processName1, processName2)
                    scheduler.util.editor.connection(self.graph, processName2, processName3)
                    # -- IIPs
                    scheduler.util.editor.iip(self.graph, 'kick', processName1)
                    # Run the graph
                    network = scheduler.network.new(self.graph)
                    scheduler.network.start(network)
                    scheduler.network.stop(network)
                    
    def test_ThreeNodes(self):
        proc = Process(target=self.runThreeNodes)
        proc.start()
        proc.join()   
        self.assertEqual(0, proc.exitcode)                
    
    def test_compareWorkers(self):
        process = Process()
        thread  = Thread()
        # process == process
        test = scheduler.util.plumber.compareWorkers(process, process)
        self.assertEqual(0, test)
        # process < thread
        test = scheduler.util.plumber.compareWorkers(process, thread)
        self.assertEqual(-1, test)                
        # thread > process
        test = scheduler.util.plumber.compareWorkers(thread, process)
        self.assertEqual(1, test)                
        # thread == thread
        test = scheduler.util.plumber.compareWorkers(thread, thread)
        self.assertEqual(0, test)

    def test_start(self):
        currDir = sys.prefix
        testDir = currDir+'/graphs'
        # Load a file with three nodes
        graph = scheduler.util.editor.json2graph('{testDir}/test/fiveParallelProcessesWithInterface.json'.format(testDir=testDir))
        # Build a network from the graph
        network = scheduler.network.new(graph)
        # Kick the network
        for i in range(5):
            network['interface']['inports']['IN{num}'.format(num=i)][0].send(i) 
        # Run the network
        #scheduler.network.start(network)
        scheduler.util.plumber.start(network['processes'], network['leak'], network['name'])
        # Check the network results
        for i in range(5):
            data = network['interface']['outports']['OUT{num}'.format(num=i)][0].recv()
            self.assertEqual(data, i)
        # Tear down the network
        scheduler.network.stop(network)

    def test_connectionInfo(self):
        conn         = 'connection'
        process      = 'process'
        port         = 'port'
        parent       = 'parent'
        testConnInfo = { 'connection' : conn,
                         'process'    : process,
                         'port'       : port,
                         'parent'     : parent }
        
        connInfo = scheduler.util.plumber.connectionInfo(conn, process, port, parent=parent)
        self.assertEqual(len(connInfo), len(testConnInfo))
        for key, value in connInfo.items():
            self.assertEqual(testConnInfo[key], value)
    
    def test_newLeak(self):
        threads  = set([])
        inports  = []
        outports = []
        testConns= { 'inports'     : inports,
                     'outports'    : outports }
        testLeak = { 'connections' : testConns,
                     'threads'     : threads }
        
        leakSetValues   = scheduler.util.plumber.newLeak(inports=inports, outports=outports, threads=threads)
        leakUseDefaults = scheduler.util.plumber.newLeak()
        for leak in [leakSetValues, leakUseDefaults]:
            self.assertEqual(len(leak), len(testLeak))
            for key, value in leak.items():
                self.assertEqual(testLeak[key], value)
            self.assertEqual(len(leak['connections']), len(testConns))            
            for key, value in leak['connections'].items():
                self.assertEqual(testConns[key], value)

    def iterTestLeaks(self, testInfos):
        parentProcessName = 'foo'
        for testInfo in testInfos:
            tgtConn, srcConn = Pipe()
            leak             = scheduler.util.plumber.newLeak(inports=[], outports=[], threads=set([]))
            #leak            = scheduler.util.plumber.newLeak() # Don't do thins. It's BAD!
            # give 'proc1' a connection
            connection  = srcConn
            processName = 'proc1'
            portName    = 'out'
            isThread    = testInfo['is thread']['src']
            inport      = False #outport
            scheduler.util.plumber.append(leak, parentProcessName, connection, processName, portName, isThread, inport=inport)
            # give 'proc2' a connection
            connection  = tgtConn
            processName = 'proc2'
            portName    = 'in'
            isThread    = testInfo['is thread']['tgt']
            inport      = True
            scheduler.util.plumber.append(leak, parentProcessName, connection, processName, portName, isThread, inport=inport)
            # close the connections *NOT* used by the given process name
            processName = testInfo['process name']
            
            yield leak, tgtConn, srcConn

    def test_closeByProcess(self):
        testInfos = [{ 'is thread'    : { 'src' : False, 
                                          'tgt' : False },
                       'is closed'    : { 'src' : False, 
                                          'tgt' : True },
                       'process name' : 'proc1',
                       'error msg'    : 'Given two processes, tried to close connections not used by "proc1".'},
                     { 'is thread'    : { 'src' : True, 
                                          'tgt' : True },
                       'is closed'    : { 'src' : False, 
                                          'tgt' : False },
                       'process name' : 'proc1',
                       'error msg'    : 'Given two threads, tried to close connections not used by "proc1" (and alias "proc2").'},
                     { 'is thread'    : { 'src' : True, 
                                          'tgt' : False },
                       'is closed'    : { 'src' : True, 
                                          'tgt' : True },
                       'process name' : 'proc3',
                       'error msg'    : 'Given two workers, tried to close connections not used by non-existent "proc3"; would be *all* connections.'}]
        
        for i, (leak, tgtConn, srcConn) in enumerate(self.iterTestLeaks(testInfos)):
            scheduler.util.plumber.closeByProcess(leak, testInfos[i]['process name'])
            # check that the proper connections were closed
            self.assertEqual(srcConn.closed, testInfos[i]['is closed']['src'], testInfos[i]['error msg'])
            self.assertEqual(tgtConn.closed, testInfos[i]['is closed']['tgt'], testInfos[i]['error msg'])      
        
    def test_getLeakByProcess(self):
        testInfos = [{ 'is thread'    : { 'src' : False, 
                                          'tgt' : False },
                       'conns'        : ['srcConn'],
                       'process name' : 'proc1',
                       'threads'      : set(['proc1']),
                       'error msg'    : ''},
                     { 'is thread'    : { 'src' : True, 
                                          'tgt' : True },
                       'conns'        : ['srcConn', 'tgtConn'],
                       'process name' : 'proc1',
                       'threads'      : set(['proc1', 'proc2']),
                       'error msg'    : ''},
                     { 'is thread'    : { 'src' : True, 
                                          'tgt' : False },
                       'conns'        : [],
                       'process name' : 'rootProc',
                       'threads'      : set(['rootProc']),
                       'error msg'    : ''}]

        for i, (leak, tgtConn, srcConn) in enumerate(self.iterTestLeaks(testInfos)):
            conn = {'tgtConn' : tgtConn,
                    'srcConn' : srcConn}
            
            leakResult = scheduler.util.plumber.getLeakByProcess(leak, testInfos[i]['process name'])

            # check that the proper leaks were recieved
            connNeedSet = set([conn[key] for key in testInfos[i]['conns']])
            connHaveSet = set([])
            for portType in ['inports', 'outports']:
                for connInfo in leakResult['connections'][portType]:
                    connHaveSet.add(connInfo['connection'])
            self.assertEqual(len(connHaveSet), len(connNeedSet))
            self.assertSetEqual(connHaveSet, connNeedSet)
            self.assertSetEqual(leakResult['threads'], testInfos[i]['threads'])

    def test_append(self):
        tgtConn, srcConn = Pipe()
        leak             = scheduler.util.plumber.newLeak(inports=[], outports=[], threads=set([]))
        #leak            = scheduler.util.plumber.newLeak() # Don't do thins. It's BAD!
        # Add an in-port to a Process 
        connection  = srcConn
        processName = 'proc1'
        portName    = 'out'
        isThread    = False
        inport      = False #outport
        parent      = 'parentProc1'
        FIRST_ELEM  = 0
        scheduler.util.plumber.append(leak, parent, connection, processName, portName, isThread, inport=inport)
        self.assertEqual(srcConn, leak['connections']['outports'][FIRST_ELEM]['connection'])
        self.assertEqual(parent, leak['connections']['outports'][FIRST_ELEM]['parent'])
        self.assertFalse('proc1' in leak['threads'])
        # Add an out-port to a Thread
        connection  = tgtConn
        processName = 'proc2'
        portName    = 'in'
        isThread    = True
        inport      = True
        parent      = 'parentProc1'
        FIRST_ELEM  = 0
        scheduler.util.plumber.append(leak, parent, connection, processName, portName, isThread, inport=inport)
        self.assertEqual(tgtConn, leak['connections']['inports'][FIRST_ELEM]['connection'])
        self.assertEqual(parent, leak['connections']['inports'][FIRST_ELEM]['parent'])
        self.assertTrue('proc2' in leak['threads'])
        # Add parent node
        SECOND_ELEM  = 1
        processName  = 'parentProc1'
        scheduler.util.plumber.append(leak, parent, connection, processName, portName, isThread, inport=inport)
        self.assertEqual(None, leak['connections']['inports'][SECOND_ELEM]['parent'])
              
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_plumber')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()