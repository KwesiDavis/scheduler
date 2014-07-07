Scheduler
======
A Python implementation of FBP guided by concepts in 
["Flow-Based Programming"](http://www.jpaulmorrison.com/fbp/1stedchaps.html) by John Paul Morrison

Installing
======
Requires Python 2.6

Running
======
1. Run Scheduler
   ```
   python scheduler.py
   ```
2. Debug Scheduler with desired log-level ('INFO', 'WARN', 'DEBUG')
   ```
   python protoflo.py -log INFO
   ```
3. Debug Scheduler and run the would-be parallel processes in serial
   ```
   python protoflo.py -log DEBUG -sync
   ```

Status
=======
prototype

Can run 'Addition' components and display logs of network activity.

License
=======
MIT


TODO:
======
* Lots to-do...
