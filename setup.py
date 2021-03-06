from distutils.core import setup

setup(
    name='Scheduler',
    version='0.1.0',
    author='Kwesi Davis',
    author_email='kwesi.a.davis@gmail.com',
    packages=['scheduler', 
              'scheduler.component',
              'scheduler.component.elementary',              
              'scheduler.util',
              'scheduler.util.test'],
    scripts=['bin/run_scheduler.py'],
    data_files=[ ( 'graphs/test', ['graphs/test/subnet.json',
                                   'graphs/test/usesOneSubnet.json',
                                   'graphs/test/twoProcesses.json',
                                   'graphs/test/twoProcessesWithMetadata.json',
                                   'graphs/test/twoProcessesWithConfig.json',
                                   'graphs/test/fiveParallelProcessesWithInterface.json'
                                   ] ),
                 ( 'graphs'     , ['graphs/add_tree.json',
                                   'graphs/merge_test.json'] )],
    url='http://pypi.python.org/pypi/Scheduler/',
    license='LICENSE.txt',
    description='A Python implementation of a FBP framework guided by concepts in "Flow-Based Programming" by John Paul Morrison.',
    long_description=open('README.md').read(),
    install_requires=[
        "argparse >= 1.2.1",
        "networkx >= 1.9",
        "numpy >= 1.8.1",
        "matplotlib >= 1.3.1",
        "pygraphviz >= 1.2"
    ],
)
