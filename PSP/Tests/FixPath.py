"""Fix the Python path to start with our Webware parent directory.

Merely importing this module fixes the path.

Doing this _guarantees_ that we're testing our local classes and not some other
installation. For those of us who have multiple instances of Webware present,
this is critical. For those who do not, this doesn't hurt anything.
"""

import sys
from os.path import abspath, dirname

webwarePath = dirname(dirname(dirname(abspath(__file__))))
if sys.path[0] != webwarePath:
    sys.path.insert(0, webwarePath)
