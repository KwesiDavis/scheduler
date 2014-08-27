import scheduler.util.editor
import scheduler.util.debug
import scheduler.util.plot
import unittest, sys, shlex
from subprocess import Popen, PIPE

class TestDebug(unittest.TestCase):
    
    def test_AddTree(self):
        cmd  = 'python {prefix}/bin/run_scheduler.py -file {prefix}/graphs/add_tree.json -sync'.format(prefix=sys.prefix)
        args = shlex.split(cmd)
        p    = Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        (_, stderrdata) = p.communicate(input='one\ntwo\nthree\nfour\n')
        errorCode = p.wait()
        self.assertEqual(0, errorCode, stderrdata)

    def test_UsesOneSubnet(self):
        cmd  = 'python {prefix}/bin/run_scheduler.py -file {prefix}/graphs/test/usesOneSubnet.json -sync'.format(prefix=sys.prefix)
        args = shlex.split(cmd)
        p    = Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        (_, stderrdata) = p.communicate(input='one\ntwo\nthree\n')
        errorCode = p.wait()
        self.assertEqual(0, errorCode, stderrdata)
    
    def test_add(self):
        currDir = sys.prefix
        testDir = currDir+'/graphs'
        # Load a file with three nodes
        jsonGraph = scheduler.util.editor.json2graph('{testDir}/add_tree.json'.format(testDir=testDir))
        # Add the debugging nodes
        jsonGraph = scheduler.util.debug.add(jsonGraph)
        # Build a Networkx graph to query topology 
        G = scheduler.util.plot.json2networkx(jsonGraph, name='*main*', root=False)
 
        # There are eight nodes: add1, add2, add3, info,
        #                        events, stdin, sync, unblock
        self.assertEqual(8, G.number_of_nodes())
        # Search for the Merge node
        for nodeIdx in range(G.number_of_nodes()):
            try:
                compName = G.node[nodeIdx]['component']
            except KeyError:
                continue
            if 'Merge' == compName:
                # Check that all nodes are feeding into the Merge node
                eventsMergeIdx = nodeIdx
                setKnown = set([u'info', u'add3', u'add2', u'add1'])
                setTest  = set([ G.node[i]['process'] for i in G.predecessors(eventsMergeIdx) ])
                self.assertEqual(setKnown, setTest)
                # Check that merge feeds into the 'sync' (or Join)
                setKnown = set(['*sync*'])
                setTest  = set([ G.node[i]['process'] for i in G.successors(eventsMergeIdx) ])
                self.assertEqual(setKnown, setTest)
                # Check that standard-in and event messages are going into 
                # the 'sync' node
                syncJoinIdx = G.successors(eventsMergeIdx)[0]
                setKnown = set(['*stdin*', '*events*'])
                setTest  = set([ G.node[i]['process'] for i in G.predecessors(syncJoinIdx) ])
                self.assertEqual(setKnown, setTest)
                # Check that the 'sync' node feeds into the 'unblock' node
                setKnown = set(['*unblock*'])
                setTest  = set([ G.node[i]['process'] for i in G.successors(syncJoinIdx) ])
                self.assertEqual(setKnown, setTest)
                break
        
    def setUp(self):
        pass
        
def suite():
    suite = unittest.TestLoader().loadTestsFromName('scheduler.util.test.test_debug')
    return suite

if __name__ == '__main__':
    suite = suite()
    suite.debug()