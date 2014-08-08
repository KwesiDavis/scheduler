Scheduler
======
A Python implementation of FBP guided by concepts in 
["Flow-Based Programming"](http://www.jpaulmorrison.com/fbp/1stedchaps.html) by John Paul Morrison

Installing
======

#### Using Python 2.7

#### Get virtualenv

On Ubuntu:
* Launch theUbuntu Software Center
* Search for 'virtualenv' and install it

#### Create a virtual environment

(see http://docs.python-guide.org/en/latest/dev/virtualenvs/)
* Note: This causes 'setuptools' and 'pip' to get installed in the virtual environment.
```
mkdir enviroments
cd enviroments/
virtualenv venv
```

#### Activate virtual environment

```
source ./venv/bin/activate
```
* Note: If not using bash, run ```bash``` command before sourcing the activate script.

#### Install dependencies (into virtual environment)

On Ubuntu:
* Launch theUbuntu Software Center
* Search for and install the following tools:
```
python-dev
libfreetype6-dev
graphviz
libgraphviz-dev
```

Install the following Python packages:
* Note: If not using '-plot' option 'networkx', 'numpy', 'matplotlib', 'pygraphiz' not required.
```
pip install networkx
pip install numpy
pip install matplotlib
pip install pygraphiz
```

#### Build Scheduler (into virtual environment)

```
git clone https://github.com/KwesiDavis/scheduler.git Scheduler
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

####  Synchronize 

Synchronize the start of every process to the 'Enter'-key to step through execution serially:

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
