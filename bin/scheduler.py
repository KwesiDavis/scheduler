#!/usr/local/bin/python
import sys
sys.path.insert(0, '/usr/pic1/noflo/projects/actionflow/github/scheduler/')

import logging, argparse
import scheduler.engine

if __name__ == '__main__':
    # parse command-line args
    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('-file', type=str, help='Graph file to run.', required=True)
    parser.add_argument('-loglevel', type=str, help='Set the log level', default="WARN")
    parser.add_argument('-logfile', type=str, help='Redirect log entries to a file.', default=None)
    parser.add_argument('-sync', help='Step over processes, one-by-one, with the "Enter" key.', action="store_true")    
    args = parser.parse_args(sys.argv[1:])
    # set the log level
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % numeric_level)
    logging.basicConfig(level=numeric_level, filename=args.logfile, filemode='w')
    # Run the engine
    scheduler.engine.run(args.file, sync=args.sync)
