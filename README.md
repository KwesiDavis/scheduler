Scheduler
======
A Python implementation of FBP guided by concepts in 
["Flow-Based Programming"](http://www.jpaulmorrison.com/fbp/1stedchaps.html) by John Paul Morrison

Installing
======
#### Using Python 2.6

#### Get virtualenv 
(see https://virtualenv.pypa.io/en/latest/virtualenv.html#installation)
```
mkdir downloads/virtualenv/
cd downloads/virtualenv/
curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz
tar xvfz virtualenv-1.11.6.tar.gz
cd virtualenv-1.11.6/
/usr/bin/python setup.py install --user
```
#### Create a virtual environment 
(see http://docs.python-guide.org/en/latest/dev/virtualenvs/)
* Note: This causes 'setuptools' and 'pip' to get installed in the virtual environment.
```
mkdir enviroments
cd enviroments/
/usr/home/<user_name>/.local/bin/virtualenv venv
```
#### Activate virtual environment
```
bash
source ./venv/bin/activate
```
#### Install dependencies (into virtual environment)
* Note: If using Python 2.7 or above 'argparse' is not required.
* Note: If not using '-plot' option 'networkx', 'numpy', 'matplotlib' not required.
```
pip install argparse
pip install networkx
pip install numpy
pip install matplotlib
```
#### Build Scheduler (into virtual environment)
```
cd Scheduler
python setup.py install --record installed_files.txt
```

Running
======
####  Run Scheduler on a JSON graph file.
```
python run_scheduler.py -file /path/to/my/graph.json
```
####  Set Scheduler to desired log-level: 'INFO', 'WARN', 'DEBUG', etc.
```
python run_scheduler.py -file /path/to/my/graph.json -loglevel info
```
####  Write Scheduler log to disk instead of console.
```
python run_scheduler.py -file /path/to/my/graph.json -logfile /path/to/my/log.txt
```
####  Draw an image of the network Scheduler is running.
```
python run_scheduler.py -file /path/to/my/graph.json -plot /path/to/my/image.png
```
####  Synchronize the start of every process to the 'Enter'-key to step through execution serially.
```
python run_scheduler.py -file /path/to/my/graph.json -sync
```

Status
=======
prototype

* Can execute a network of components.
* Can display (and write) debug logs of network activity.
* Can synchronize processes to run serially instead of in parallel. 

License
=======
MIT


TODO:
======
* Lots to-do...
