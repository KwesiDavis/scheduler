#!/usr/local/bin/python
import sys
sys.path.insert(0, '/usr/pic1/noflo/projects/actionflow/github/scheduler/')

import logging, argparse
import scheduler.network
import scheduler.util.editor
import scheduler.util.iip
import scheduler.util.debug

def parseArgs():
    # add cmd line options
    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('-file', type=str, help='Graph file to run.', required=True)
    parser.add_argument('-loglevel', type=str, help='Set the log level', default="WARN")
    parser.add_argument('-logfile', type=str, help='Redirect log entries to a file.', default=None)
    parser.add_argument('-sync', help='Step over processes, one-by-one, with the "Enter" key.', action="store_true")    
    parser.add_argument('-plot', type=str, help='Write a plot of the graph to a PNG file.', default=None)
    # parse command-line args
    args = parser.parse_args(sys.argv[1:])    
    return args

def setupLogging(levelStr, filename):
    # Convert logging level name to enum value
    attrName = levelStr.upper() # 'INFO', 'WARN', 'DEBUG', etc.
    level    = getattr(logging, attrName, None)
    if not isinstance(level, int):
        raise ValueError('Invalid log level: %s' % level)
    # Set log level and optional log file
    logging.basicConfig(level=level, filename=filename, filemode='w')

def main():
    args = parseArgs()
    setupLogging(level=args.loglevel, file=args.logfile)
    # Load a graph from disk
    graph = scheduler.util.editor.json2graph(args.file)
    # Extract IIPs that are embedded in the 
    # graph and apply them via a special IIP-process
    graph = scheduler.util.iip.addFromGraph(graph)
    # Synchronize two events:
    #  1) a process getting all its inputs
    #  2) the user hitting 'Enter' the key
    if args.sync:
        graph = scheduler.util.debug.add(graph)
    # Plot the graph we are about to run
    pngFilename = args.plot
    if pngFilename:
        import scheduler.util.plot # slow to import; do only if needed  
        G = scheduler.util.plot.json2networkx(graph, 'untitled')
        scheduler.util.plot.networkx2png(G, pngFilename)
    # Build a network from the graph
    network = scheduler.network.new(graph)
    # Run the network
    scheduler.network.start(network)
    # Tear down the network
    scheduler.network.stop(network)    

if __name__ == '__main__':
    main()