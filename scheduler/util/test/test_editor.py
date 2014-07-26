import scheduler.util.editor
import unittest

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
    #unittest.main()
    suite = suite()
    unittest.TextTestRunner(verbosity=2).run(suite)