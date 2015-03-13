"""
PyLmod is a module that implements MIT Learning Modules API in Python
"""

import os.path
from pkg_resources import get_distribution, DistributionNotFound

from pylmod.client import Client
from pylmod.gradebook import GradeBook
from pylmod.membership import Membership
import requests  # see if adding this import will fix RTD build

# pylint: disable=no-member
try:
    DIST = get_distribution('pylmod')
    # Normalize case for Windows systems
    DIST_LOC = os.path.normcase(DIST.location)
    print('distribution location is <%s>' % DIST_LOC)  # debug
    HERE = os.path.normcase(__file__)
    print('cwd is <%s>' % HERE)  # debug
    if not HERE.startswith(
            os.path.join(DIST_LOC, 'pylmod')
    ):  # pragma: no cover
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:  # pragma: no cover
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = DIST.version


__all__ = ['Client', 'GradeBook', 'Membership']
