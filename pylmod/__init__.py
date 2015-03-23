"""
PyLmod is a module that implements MIT Learning Modules API in Python
"""
import os.path
from pkg_resources import get_distribution, DistributionNotFound

from pylmod.gradebook import GradeBook
from pylmod.membership import Membership


def _get_version():
    """Grab version from pkg_resources"""
    # pylint: disable=no-member
    try:
        dist = get_distribution(__project__)
    except DistributionNotFound:
        return 'Please install this project with setup.py'
    else:
        return dist.version

__all__ = ['GradeBook', 'Membership']
__project__ = 'pylmod'
__version__ = _get_version()
