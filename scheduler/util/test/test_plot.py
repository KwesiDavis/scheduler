import scheduler.util.plot
import scheduler.util.editor
import scheduler.network
import unittest, sys

class TestPlot(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_processInfo(self):
        # build a graph with one process
        processName   = 'processName'
        componentName = 'componentName'
        config        = { 'bar' : 'my config info' }
        metadata      = { 'foo' : 'my metadata info' }
        graph         = scheduler.util.editor.newGraph()
        scheduler.util.editor.process(graph, processName, componentName, config, metadata)
        # extract info from the new process and verify the extraction 
        # occurred properly
        # -- put both config info and metadata in one dict
        data = {'config':config}
        data.update(metadata)
        networkxId = 1
        knownAttr  = { 'component'  : componentName,
                       'isSubNet'   : componentName == 'SubNet',
                       'process'    : processName,
                       'metadata'   : data,
                       'networkxId' : networkxId }
        FIRST_ELEM = 0
        process    = graph['processes'].items()[FIRST_ELEM]
        attr       = scheduler.util.plot.processInfo(process, networkxId=networkxId)
        self.assertDictEqual(knownAttr, attr)
    
    def test_connectionInfo(self):
        # build a graph with one connection
        srcProc = 'srcProcess'
        srcPort = 'srcPort'
        tgtProc = 'tgtProcess'
        tgtPort = 'tgtPort'
        graph   = scheduler.util.editor.newGraph()
        src     = (srcProc, srcPort)
        tgt     = (tgtProc, tgtPort)
        scheduler.util.editor.connection(graph, src, tgt)
        # extract info from the new connection and verify the extraction 
        # occurred properly 
        FIRST_ELEM = 0
        connection = graph['connections'][FIRST_ELEM]
        (edge, edgeAttributes) = scheduler.util.plot.connectionInfo(connection)
        self.assertEqual((srcProc, tgtProc), edge)
        self.assertEqual((('src',  srcPort), ('tgt', tgtPort)), edgeAttributes)
    
    def test_exportInfo(self):
        internalProcessName = 'process1'
        
        tests = [{ 'external port name' : 'IN',
                   'internal port name' : 'in',
                   'tgt'                : internalProcessName,
                   'is inport'          : True },
                 { 'external port name' : 'OUT',
                   'internal port name' : 'out',
                   'tgt'                : internalProcessName,
                   'is inport'          : False }]
        
        portType = { True  : 'inports',
                     False : 'outports' }
        
        for test in tests: 
            extPortName = test['external port name']
            intPortName = test['internal port name']
            tgt         = test['tgt']
            isInport    = test['is inport']
            graph       = scheduler.util.editor.newGraph()
            scheduler.util.editor.export(graph, extPortName, tgt, isInport)
            # extract info from the newly exported port and verify the extraction 
            # occurred properly 
            FIRST_ELEM = 0
            exportType = 'inports'
            root       = 'parentProcess1'
            export     = graph[portType[isInport]].items()[FIRST_ELEM]        
            (edge, edgeAttributes) = scheduler.util.plot.exportInfo(export, exportType, root=root)
            self.assertEqual((root, internalProcessName), edge)
            self.assertEqual((('src',  extPortName), ('tgt', intPortName)), edgeAttributes)
            
    def test_json2networkx(self):
        currDir          = sys.prefix
        graphDir         = currDir+'/graphs'
        addTreeJsonFile  = '{graphDir}/add_tree.json'.format(graphDir=graphDir)
        addTreeJsonGraph = scheduler.util.editor.json2graph(addTreeJsonFile)
        subnetJsonFile   = '{graphDir}/test/subnet.json'.format(graphDir=graphDir)
        subnetJsonGraph  = scheduler.util.editor.json2graph(subnetJsonFile)       
        
        tests = [ { 'graph'           : addTreeJsonGraph,
                    'is root enabled' : False,
                    'num nodes'       : len(addTreeJsonGraph['processes'].items()),
                    'num exports'     : len(addTreeJsonGraph['inports'].items()) + len(addTreeJsonGraph['outports'].items()),
                    'num edges'       : len(list(scheduler.network.connectionIter(addTreeJsonGraph, iips=False))) },
                  { 'graph'           : subnetJsonGraph,
                    'is root enabled' : True,
                    'num nodes'       : len(subnetJsonGraph['processes'].items()) + 1,
                    'num exports'     : len(subnetJsonGraph['inports'].items()) + len(subnetJsonGraph['outports'].items()),
                    'num edges'       : len(list(scheduler.network.connectionIter(subnetJsonGraph, iips=False))) + len(subnetJsonGraph['inports'].items()) + len(subnetJsonGraph['outports'].items()) } ]
        
        for test in tests:
            isRootEnabled = test['is root enabled']
            graph         = test['graph']
            numNodes      = test['num nodes']
            numExports    = test['num exports']
            numEdges      = test['num edges']
            
            G = scheduler.util.plot.json2networkx(graph, name='*main*', root=isRootEnabled)
            self.assertEqual(numNodes,   G.number_of_nodes())
            self.assertEqual(numExports, len(G.graph['export']))
            self.assertEqual(numEdges,   G.number_of_edges())
    
    def test_networkx2png(self):
        import tempfile, shutil, os
        currDir         = sys.prefix
        graphDir        = currDir+'/graphs'
        addTreeJsonFile = '{graphDir}/add_tree.json'.format(graphDir=graphDir)
        graph           = scheduler.util.editor.json2graph(addTreeJsonFile)
        tmpDir          = tempfile.mkdtemp()
        filename        = tmpDir + '/foo.png'
        G = scheduler.util.plot.json2networkx(graph, name='*main*', root=False)
        try:
            scheduler.util.plot.networkx2png(G, filename)
            self.assertTrue(os.path.exists(filename))
        finally:
            shutil.rmtree(tmpDir)
    
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_plot')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()