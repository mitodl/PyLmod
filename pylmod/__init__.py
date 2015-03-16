"""
PyLmod is a module that implements MIT Learning Modules API in Python
"""
import os.path
from pkg_resources import get_distribution, DistributionNotFound

from pylmod.client import Client
from pylmod.gradebook import GradeBook
from pylmod.membership import Membership


def _get_version():
    """Grab version from pkg_resources"""
    # pylint: disable=no-member
    try:
        dist = get_distribution(__project__)
        # Normalize case for Windows systems
        dist_loc = os.path.normcase(dist.location)
        here = os.path.normcase(os.path.abspath(__file__))
        if not here.startswith(
                os.path.join(dist_loc, __project__)
        ):
            # not installed, but there is another version that *is*
            raise DistributionNotFound
    except DistributionNotFound:
        return 'Please install this project with setup.py'
    else:
        return dist.version

__all__ = ['Client', 'GradeBook', 'Membership']
__project__ = 'pylmod'
__version__ = _get_version()
