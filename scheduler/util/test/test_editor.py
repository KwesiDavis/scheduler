import scheduler.util.editor
import unittest, sys

class TestEditor(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def test_json2graph(self):
        currDir = sys.prefix
        testDir = currDir+'/graphs'
        # Load a file with four nodes
        jsonGraph = scheduler.util.editor.json2graph('{testDir}/add_tree.json'.format(testDir=testDir))
        # Check graph content
        self.assertIsInstance(jsonGraph, dict)
        self.assertEqual(7, len(jsonGraph['connections']))
        self.assertEqual(4, len(jsonGraph['processes']))
        self.assertEqual(0, len(jsonGraph['inports']))
        self.assertEqual(0, len(jsonGraph['outports']))
    
    def test_setConfig(self):
        currDir = sys.prefix
        testDir = currDir+'/graphs'
        key = 'foo'
        value = 'bar'
        configData = {key:value}
        processName = 'add1'
        jsonGraph = scheduler.util.editor.json2graph('{testDir}/add_tree.json'.format(testDir=testDir))
        scheduler.util.editor.setConfig(jsonGraph, processName, configData)
        self.assertEqual(value, jsonGraph['processes'][processName]['metadata']['config'][key])
    
    def _getProcs(self, graph):
        '''
        returns a list of name pairs: [(processName, componentName), ...]
        '''
        getNamePair = lambda x:(x[0], x[1]['component'])
        namePairs   = map(getNamePair, graph.get('processes', {}).items())
        return namePairs 
    
    def test_process(self):
        currDir      = sys.prefix
        testDir      = currDir+'/graphs/test'
        
        graphFxns = { 'garbage'        : lambda : None,
                      'empty'          : lambda : {},
                      'twoProcs'       : lambda : scheduler.util.editor.json2graph('{testDir}/twoProcesses.json'.format(testDir=testDir)),
                      'twoProcsMeta'   : lambda : scheduler.util.editor.json2graph('{testDir}/twoProcessesWithMetadata.json'.format(testDir=testDir)),
                      'twoProcsConfig' : lambda : scheduler.util.editor.json2graph('{testDir}/twoProcessesWithConfig.json'.format(testDir=testDir)) }
        processNames = { 'garbage' : None,
                         'empty'   : '',
                         'fake'    : 'foo',
                         'real'    : 'testNoop1' }
        componentNames = { 'garbage' : None,
                           'empty'   : '',
                           'fake'    : 'Foo',
                           'real'    : 'NoOp' }
        metadataFxns = { 'garbage' : lambda : None,
                         'empty'   : lambda : {},
                         'generic' : lambda : { 'int'   : 7,
                                                'str'   : 'Hello, World!',
                                                'tuple' : (3.14, True, None) } }
        for graphFxnKey, graphFxn in graphFxns.items():
            for processNameKey, processName in processNames.items():
                for componentNameKey, componentName in componentNames.items():
                    for metadataFxnKey, metadataFxn in metadataFxns.items():
                        for configFxnKey, configFxn in metadataFxns.items():
                            graph    = graphFxn()
                            fxn      = scheduler.util.editor.process
                            args     = (graph, processName, componentName)
                            kwargs   = {'metadata' : metadataFxn(), 'config' : configFxn()}
                            
                            if 'garbage' == graphFxnKey:
                                exc = AttributeError
                                self.assertRaises(exc, fxn, *args, **kwargs)
                            else:
                                if False:
                                    print graphFxnKey, processNameKey, componentNameKey, metadataFxnKey, configFxnKey
                                
                                procsBefore = set(self._getProcs(graph))
                                fxn(*args, **kwargs)
                                procsAfter = set(self._getProcs(graph))
                                
                                procsExpectedDiff = set([(processName, componentName)])
                                procsActualDiff   = procsAfter-procsBefore
                                
                                self.assertEqual(procsExpectedDiff, procsActualDiff)
    
    def test_connection(self):
        graph   = scheduler.util.editor.newGraph()
        sources = ['process1', ('process1', 'out')]
        targets = ['process2', ('process2', 'in')]
        for src in sources:
            for tgt in targets:
                scheduler.util.editor.connection(graph, src, tgt)
                connection = graph['connections'][0]
                self.assertEqual('process1', connection['src']['process'])
                self.assertEqual('out',      connection['src']['port'])
                self.assertEqual('process2', connection['tgt']['process'])
                self.assertEqual('in',       connection['tgt']['port'])
    
    def test_modify(self):
        inportInfos      = [('inports'    ,{}), None]
        outportInfos     = [('outports'   ,{}), None]
        processesInfos   = [('processes'  ,{}), None]
        connectionsInfos = [('connections',[]), None]
        graph = {}
        for inportInfo in inportInfos:
            for outportInfo in outportInfos:
                for processesInfo in processesInfos:
                    for connectionsInfo in connectionsInfos:
                        edits = {}
                        if inportInfo:
                            inportKey, inportValue = inportInfo
                            edits.setdefault(inportKey, inportValue)
                        if outportInfo:
                            outportKey, outportValue = outportInfo
                            edits.setdefault(outportKey, outportValue)            
                        if processesInfo:
                            processesportKey, processesValue = processesInfo
                            edits.setdefault(processesportKey, processesValue)
                        if connectionsInfo:
                            connectionsKey, connectionsValue = connectionsInfo
                            edits.setdefault(connectionsKey, connectionsValue)            
                            
                        graph = {}
                        scheduler.util.editor.modify(graph, edits)
                        self.assertDictEqual(graph, edits, "{inports} {outports} {processes} {connections}".format(inports=inportInfo, 
                                                                                                                   outports=outportInfo, 
                                                                                                                   processes=processesInfo, 
                                                                                                                   connections=connectionsInfo))
    
    def test_newGraph(self):
        graph = scheduler.util.editor.newGraph()
        self.assertEqual(graph['processes']  , {})
        self.assertEqual(graph['connections'], [])
        self.assertEqual(graph['inports']    , {})
        self.assertEqual(graph['outports']   , {})
    
    def test_iip(self):
        graph   = scheduler.util.editor.newGraph()
        targets = ['process2', ('process2', 'in')]
        data    = 'foo'
        for tgt in targets:
            scheduler.util.editor.iip(graph, data, tgt)
            connection = graph['connections'][0]
            self.assertEqual(data,       connection['data'])
            self.assertEqual('process2', connection['tgt']['process'])
            self.assertEqual('in',       connection['tgt']['port'])
            
    def test_export(self):
        graph    = scheduler.util.editor.newGraph()
        targets  = ['process2', ('process2', 'in')]
        portName = 'port1'
        
        tests = [{ 'tgt'       : 'process2',
                   'portName'  : 'port1',
                   'is inport' : True },
                 { 'tgt'       : ('process2', 'out'),
                   'portName'  : 'port2',
                   'is inport' : False }]
        portType = { True  : 'inports',
                     False : 'outports' }
        defaultPortName = { True  : 'in',
                            False : 'out' }        
        for test in tests:
            graph    = scheduler.util.editor.newGraph()
            portName = test['portName']
            tgt      = test['tgt']
            isInport = test['is inport']
            scheduler.util.editor.export(graph, portName, tgt, isInport)
            
            self.assertEqual(graph[portType[isInport]][portName]['process'], 'process2')
            self.assertEqual(graph[portType[isInport]][portName]['port'],    defaultPortName[isInport])
            
    
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_editor')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()