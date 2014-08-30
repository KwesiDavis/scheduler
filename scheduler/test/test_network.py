import unittest, sys
import scheduler.network
import scheduler.util.editor
from multiprocessing import Pipe

class TestNetwork(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_connectionIter(self):
        tests = [{ 'num conns' : 8,
                   'num iips'  : 4 },
                 { 'num conns' : 0,
                   'num iips'  : 4 },
                 { 'num conns' : 8,
                   'num iips'  : 0 }]
        
        for test in tests:
            iips     = test['num iips'] > 0
            graph    = scheduler.util.editor.newGraph()
            numConns = test['num conns']
            numIIPs  = test['num iips']
            # add some connections 
            for i in range(numConns):
                src, tgt = 'proc{index}'.format(index=i), 'proc{index}'.format(index=i+1)
                scheduler.util.editor.connection(graph, src, tgt)
            # add some iips 
            for i in range(numIIPs):
                data, tgt = i, 'proc{index}'.format(index=i)
                scheduler.util.editor.iip(graph, data, tgt)
            # check for proper number of connections
            generator = scheduler.network.connectionIter(graph, iips=iips)
            self.assertEqual(numConns+numIIPs, len(list(generator)))
            # check that the right amount of data comes out
            numData = 0
            for connInfo in scheduler.network.connectionIter(graph, iips=iips):
                (_, _, dataInfo)   = connInfo
                (isDataUsed, data) = dataInfo
                if isDataUsed: 
                    numData += 1
            self.assertEqual(numIIPs, numData)
    
    def test_exportIter(self):
        graph    = scheduler.util.editor.newGraph()
        numInPorts  = 8
        numOutPorts = 4
        # add some in-ports 
        for i in range(numInPorts):
            portName = 'IN{index}'.format(index=i)
            tgt      = 'proc{index}'.format(index=i)
            isInport = True
            scheduler.util.editor.export(graph, portName, tgt, isInport)
        # add some out-ports 
        for i in range(numOutPorts):
            portName = 'OUT{index}'.format(index=i)
            tgt      = 'proc{index}'.format(index=i)
            isInport = False
            scheduler.util.editor.export(graph, portName, tgt, isInport)
        # check for proper number of connections
        parentProcessName = 'foo'
        generator         = scheduler.network.exportIter(graph, parentProcessName)
        self.assertEqual(numInPorts+numOutPorts, len(list(generator)))
        # check that the right amount of data comes out
        numData       = 0
        countInports  = 0
        countOutports = 0
        for connInfo in scheduler.network.exportIter(graph, parentProcessName):
            (srcInfo, tgtInfo, dataInfo)  = connInfo
            (srcProcessName, _) = srcInfo
            (tgtProcessName, _) = tgtInfo
            (isDataUsed,     _)        = dataInfo
            if srcProcessName == parentProcessName: 
                countInports += 1
            if tgtProcessName == parentProcessName:
                countOutports += 1
            if isDataUsed:
                numData += 1
        self.assertEqual(0, numData)
        self.assertEqual(countInports, numInPorts)
        self.assertEqual(countOutports, numOutPorts)
    
    def test_new(self):
        prefix = sys.prefix
        tests = [ { 'name'           : 'SubNet load test; ignore IIPs in graph file.',
                    'args'           : { 'dir'      : 'graphs',
                                         'basename' : 'add_tree.json',
                                         'name'     : 'networkName',
                                         'iips'     : False,
                                         'leak'     : scheduler.util.plumber.newLeak() },
                    'expectedResult' : { 'processes'     : range(4),
                                         'interface'     : {'inports':set([]), 'outports':set([])},
                                         'leak threads'  : set(['networkName']),
                                         'leak inports'  : range(3),
                                         'leak outports' : range(3) } },
                  { 'name'           : 'Root network load test; apply IIPs in graph file.',
                    'args'           : { 'dir'      : 'graphs',
                                         'basename' : 'add_tree.json',
                                         'name'     : 'networkName',
                                         'iips'     : True,
                                         'leak'     : scheduler.util.plumber.newLeak() },
                    'expectedResult' : { 'processes'     : range(4),
                                         'interface'     : {'inports':set([]), 'outports':set([])},
                                         'leak threads'  : set(['networkName']),
                                         'leak inports'  : range(7),
                                         'leak outports' : range(7) } },
                  { 'name'           : 'Graph has threads and external interface.',
                    'args'           : { 'dir'      : 'graphs/test',
                                         'basename' : 'fiveParallelProcessesWithInterface.json',
                                         'name'     : 'networkName',
                                         'iips'     : False,
                                         'leak'     : scheduler.util.plumber.newLeak() },
                    'expectedResult' : { 'processes'     : range(5),
                                         'interface'     : { 'inports'  : set(['IN0','IN1','IN2','IN3', 'IN4']), 
                                                             'outports' : set(['OUT0','OUT1','OUT2','OUT3', 'OUT4'])},
                                         'leak threads'  : set(['networkName', 'proc1', 'proc3']),
                                         'leak inports'  : range(10),
                                         'leak outports' : range(10) } } ]        
        for test in tests:
            args          = test['args']
            expectedResult = test['expectedResult']  
            graph          = scheduler.util.editor.json2graph('{prefix}/{dir}/{basename}'.format(prefix=prefix, dir=args['dir'], basename=args['basename']))
            result         = scheduler.network.new(graph, args['name'], args['iips'], args['leak'])
            # check network name
            self.assertEqual(args['name'], result['name'])
            # check processes
            self.assertEqual(len(expectedResult['processes']), len(result['processes']))
            # check external ports
            self.assertSetEqual(expectedResult['interface']['inports'], set(result['interface']['inports'].keys()))
            self.assertSetEqual(expectedResult['interface']['outports'], set(result['interface']['outports'].keys()))
            # check leaks
            self.assertEqual(set(expectedResult['leak threads']), set(result['leak']['threads']))
            try:
                self.assertEqual(len(expectedResult['leak inports']), len(result['leak']['connections']['inports']))
                self.assertEqual(len(expectedResult['leak outports']), len(result['leak']['connections']['outports']))
            except Exception, e:
                # Note: When there is an external interface, the external 
                #       in-ports are effectively out-ports for the internal
                #       network and we appear in the leak structure's 
                #       'outports' list.  A similar inversion applies to 
                #       external out-ports found in the 'inports' list.
                print '\n\nINS :',[ str('{0}.{1}'.format(connInfo['process'],connInfo['port'])) for connInfo in result['leak']['connections']['inports']]
                print 'OUTS:',[ str('{0}.{1}'.format(connInfo['process'],connInfo['port'])) for connInfo in result['leak']['connections']['outports']], '\n'
                raise e
        
    def isAnyConnection(self, network, isOpen=True):
        isConnClosed = lambda x:x.closed
        isConnOpen   = lambda x:not x.closed
        getState     = { False : isConnClosed,
                         True  : isConnOpen }
        portTypes    = ['inports', 'outports']
        for portType in portTypes: 
            for _, conns in network['interface'][portType].items():
                for conn in conns:
                    if getState[isOpen](conn):
                        return True
        return False
       
    def test_start(self):
        # Note: This logic was taken from:
        #       scheduler.util.test.test_plumber.TestPlumber.test_start()
        currDir = sys.prefix
        testDir = currDir+'/graphs'
        # Load a file with three nodes
        graph = scheduler.util.editor.json2graph('{testDir}/test/fiveParallelProcessesWithInterface.json'.format(testDir=testDir))
        # Build a network from the graph
        network = scheduler.network.new(graph)
        # Check that all external interface ports are *open*
        isAnyConnClosed = self.isAnyConnection(network, isOpen=False)
        self.assertFalse(isAnyConnClosed)        
        # Kick the network
        for i in range(5):
            network['interface']['inports']['IN{num}'.format(num=i)][0].send(i) 
        # Run the network
        scheduler.network.start(network)        
        # Check the network results
        for i in range(5):
            data = network['interface']['outports']['OUT{num}'.format(num=i)][0].recv()
            self.assertEqual(data, i)
        # Tear down the network
        scheduler.network.stop(network)
                
    def test_stop(self):
        # Note: This logic was taken from:
        #       scheduler.util.test.test_plumber.TestPlumber.test_start()
        currDir = sys.prefix
        testDir = currDir+'/graphs'
        # Load a file with three nodes
        graph = scheduler.util.editor.json2graph('{testDir}/test/fiveParallelProcessesWithInterface.json'.format(testDir=testDir))
        # Build a network from the graph
        network = scheduler.network.new(graph)
        # Run the network
        scheduler.network.start(network)        
        # Tear down the network
        scheduler.network.stop(network)
        # Check that all external interface ports are *closed*
        isAnyConnOpen = self.isAnyConnection(network, isOpen=True)
        self.assertFalse(isAnyConnOpen)  
        # Check that all workers have terminated
        self.assertTrue( all([ not process.is_alive() for process in network['processes'] ]) )

    def test_closePortsByType(self):
        tgtConn, srcConn = Pipe()
        network = { 'interface': { 'inports'  : { 'IN1'  : [srcConn] },
                                   'outports' : { 'OUT1' : [tgtConn] } },
                    'name'     : 'foo' }
        
        self.assertFalse(srcConn.closed)        
        scheduler.network.closePortsByType(network, isInport=True)
        self.assertTrue(srcConn.closed)
        
        self.assertFalse(tgtConn.closed)
        scheduler.network.closePortsByType(network, isInport=False)
        self.assertTrue(tgtConn.closed)
        
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_network')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()