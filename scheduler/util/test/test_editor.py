import scheduler.util.editor
import unittest, sys

class TestProcess(unittest.TestCase):
    def setUp(self):
        self.graph = {}
        self.processes = [('foo', 'Foo'), ('bar', 'Bar'), ('boo', 'Boo'), ('far', 'Far')]
        self.data = {'int':7, 'str':'Hello, World!', 'tuple':(3.14, True, None)}
    def _checkData(self, itemsOrig, items):
        sortByKey    = lambda a,b:cmp(a[0], b[0])
        metadataOrig = sorted( itemsOrig, cmp=sortByKey)
        metadata     = sorted( items, cmp=sortByKey)
        testKeys     = []
        testValues   = []
        for zipped in zip(metadataOrig, metadata):
            ((keyOrig, valueOrig), (key, value)) = zipped
            testKeys.append(keyOrig     == key)
            testValues.append(valueOrig == value)
        return testKeys, testValues
    
class TestAllArgs(TestProcess):
    def runTest(self):
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
                                print graphFxnKey, processNameKey, componentNameKey, metadataFxnKey, configFxnKey
                                
                                procsBefore = set(self.getProcs(graph))
                                fxn(*args, **kwargs)
                                procsAfter = set(self.getProcs(graph))
                                
                                procsExpectedDiff = set([(processName, componentName)])
                                procsActualDiff   = procsAfter-procsBefore
                                
                                self.assertEqual(procsExpectedDiff, procsActualDiff)
    def getProcs(self, graph):
        '''
        returns a list of name pairs: [(processName, componentName), ...]
        '''
        getNamePair = lambda x:(x[0], x[1]['component'])
        namePairs   = map(getNamePair, graph.get('processes', {}).items())
        return namePairs 
                                
class TestNoOptionalArgs(TestProcess):
    def runTest(self):
        # make sure the shuffled sequence does not lose any elements
        for processName, componentName in self.processes:
            scheduler.util.editor.process( self.graph, processName, componentName )

        getCompName = lambda x:(x[0], x[1]['component'])
        processes   = map(getCompName, self.graph['processes'].items())
        self.assertEqual(set(processes), set(self.processes))

class TestMetadataArg(TestProcess):
    def runTest(self):
        processName, componentName = self.processes[0]
        scheduler.util.editor.process(self.graph, processName, componentName, metadata=self.data)
        
        itemsOrig = self.data.items()
        items     = self.graph['processes'][processName]['metadata'].items()
        testKeys, testValues = self._checkData(itemsOrig, items)
        
        self.assertTrue(all(testKeys))
        self.assertTrue(all(testValues))        

class TestConfigArg(TestProcess):
    def runTest(self):
        processName, componentName = self.processes[0]
        scheduler.util.editor.process(self.graph, processName, componentName, config=self.data)
        
        itemsOrig = self.data.items()
        items     = self.graph['processes'][processName]['metadata']['config'].items()
        testKeys, testValues = self._checkData(itemsOrig, items)
        
        self.assertTrue(all(testKeys))
        self.assertTrue(all(testValues))
        
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_editor')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()