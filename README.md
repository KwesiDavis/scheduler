Scheduler
======
A Python implementation of FBP guided by concepts in 
["Flow-Based Programming"](http://www.jpaulmorrison.com/fbp/1stedchaps.html) by John Paul Morrison

Installing
======
Requires Python 2.6
Requires networkx and matplotlib if graph plots are enabled.

Running
======
1. Run Scheduler on a JSON graph file.
   ```
   python scheduler.py -file /path/to/my/graph.json
   ```
2. Set Scheduler to desired log-level: 'INFO', 'WARN', 'DEBUG', etc.
   ```
   python scheduler.py -file /path/to/my/graph.json -loglevel info
   ```
3. Write Scheduler log to disk instead of console.
   ```
   python scheduler.py -file /path/to/my/graph.json -logfile /path/to/my/log.txt
   ```
4. Draw an image of the network Scheduler is running.
   ```
   python scheduler.py -file /path/to/my/graph.json -plot /path/to/my/image.png
   ```
5. Synchronize the start of every process to the 'Enter'-key to step through execution serially.
   ```
   python scheduler.py -file /path/to/my/graph.json -sync
   ```

Status
=======
prototype

Can execute a network of components.
Can display (and write) debug logs of network activity.
Can synchronize processes to run serially instead of in parallel. 

License
=======
MIT


TODO:
======
* Lots to-do...
