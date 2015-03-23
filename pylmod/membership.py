"""
Contains Membership class
"""
import logging
from pylmod.base import Base

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Membership(Base):  # pylint: disable=too-few-public-methods
    """Provide API for functions that return group membership data from
    MIT Learning Modules service.

    API reference at
    https://learning-modules-test.mit.edu/service/membership/doc.html
    """
    def __init__(
            self,
            cert,
            urlbase='https://learning-modules.mit.edu:8443/',
    ):
        super(Membership, self).__init__(cert, urlbase)
        # Add service base
        self.urlbase += 'service/membership/'
