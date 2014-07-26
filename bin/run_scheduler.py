import sys
import logging
import argparse
import scheduler.network
import scheduler.util.editor
import scheduler.util.iip
import scheduler.util.debug

def parseArgs():
    '''
    Defines command line arguments and parses them.

    Returns:
        An object with the parsed cmd line values.
    '''
    # add cmd line options
    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('-file', type=str, help='Graph file to run.', required=True)
    parser.add_argument('-loglevel', type=str, help='Sets the log level; which is "WARN" by default.', default="WARN")
    parser.add_argument('-logfile', type=str, help='Redirect log entries to a file.', default=None)
    parser.add_argument('-sync', help='Step over processes, one-by-one, with the "Enter" key.', action="store_true")    
    parser.add_argument('-plot', type=str, help='Write a plot of the graph to a PNG file.', default=None)
    # parse command-line args
    args = parser.parse_args(sys.argv[1:])    
    return args

def setupLogging(levelStr, filename):
    '''
    Given a graph and a component library generate a sub-network of Python
    multiprocessing Process objects wired to together with Pipe objects.
    
    Parameters:
        levelStr - An alias referring to a logging level ('INFO', 'info', 
                  'WARN', 'debug', etc.); internally the string is auto 
                  converted to all capital letters.
        filename - A path representing the desired location of the log file.
    '''
    # Convert logging level name to enum value
    attrName = levelStr.upper() # 'INFO', 'WARN', 'DEBUG', etc.
    level    = getattr(logging, attrName, None)
    if not isinstance(level, int):
        raise ValueError('Invalid log level: %s' % level)
    # Set log level and optional log file
    logging.basicConfig(level=level, filename=filename, filemode='w')

def main():
    '''
    Run the given network and apply any desired debug options.
    '''
    # Parse command-line args
    args = parseArgs()
    # Initialize logger
    setupLogging(args.loglevel, args.logfile)
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
        #import scheduler.util.plot # MAINT: Causes UnboundLocalError?  
        import scheduler.util.plot as plot # slow to import; do only if needed  
        G = plot.json2networkx(graph, 'untitled')
        plot.networkx2png(G, pngFilename)
    # Build a network from the graph
    network = scheduler.network.new(graph)
    # Run the network
    scheduler.network.start(network)
    # Tear down the network
    scheduler.network.stop(network)    

if __name__ == '__main__':
    main()