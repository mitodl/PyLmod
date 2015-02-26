
"""
PyLmod is a module that implements MIT Learning Modules API in python
"""
import os.path
from pkg_resources import get_distribution, DistributionNotFound

from pylmod.client import Client
from pylmod.stellargradebook import StellarGradeBook

try:
    _dist = get_distribution('pylmod')
    # Normalize case for Windows systems
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, 'pylmod')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version


__all__ = ['Client', 'StellarGradeBook', ]
