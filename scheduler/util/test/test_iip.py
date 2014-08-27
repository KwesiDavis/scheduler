#import scheduler.util.editor
#import scheduler.util.debug
import unittest, sys
import scheduler.util.editor
import scheduler.util.iip
import scheduler.util.plot

class TestIIP(unittest.TestCase):
    
    def test_addFromGraph(self):
        ROOT_IDX   = 0
        MERGE_IDX  = 1
        NOOP3_IDNX = 3
        #NOOP4_IDNX = 2
        currDir = sys.prefix
        testDir = currDir+'/graphs/test'
        jsonGraph = scheduler.util.editor.json2graph('{testDir}/subnet.json'.format(testDir=testDir))
        jsonGraph = scheduler.util.iip.addFromGraph(jsonGraph)
        G = scheduler.util.plot.json2networkx(jsonGraph, name='*main*', root=True)
        # There are four nodes: Root, Merge, NoOp3, NoOp4
        self.assertEqual(4, G.number_of_nodes())
        # Merge was inserted
        self.assertEqual('Merge', G.node[1]['component'])
        # Merge is between Root and NoOp3
        self.assertEqual([ROOT_IDX], G.predecessors(MERGE_IDX))
        self.assertEqual([NOOP3_IDNX], G.successors(MERGE_IDX))
    
    def setUp(self):
        pass
        
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_iip')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()