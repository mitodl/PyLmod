"""
PyLmod is a module that implements MIT Learning Modules API in Python
"""

import os.path
from pkg_resources import get_distribution, DistributionNotFound

from pylmod.client import Client
from pylmod.gradebook import GradeBook
from pylmod.membership import Membership

try:
    DIST = get_distribution('pylmod')
    # Normalize case for Windows systems
    DIST_LOC = os.path.normcase(DIST.location)
    HERE = os.path.normcase(__file__)
    if not HERE.startswith(os.path.join(DIST_LOC, 'pylmod')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = DIST.version


__all__ = ['Client', 'GradeBook', 'Membership']
