"""
Base class and common constants needed for pylmod tests
"""
import os
from unittest import TestCase


class BaseTest(TestCase):
    """
    Base class with convenient constants and URL endpoints for pylmod testing.
    """
    # This should be removed if we end up with common methods, but for
    # now they are just common attributes.
    # pylint: disable=too-few-public-methods
    DATA_ROOT = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'data'
    )

    CERT = os.path.join(DATA_ROOT, 'certs', 'test_cert.pem')

    URLBASE = 'https://testingstuff/'
    GRADEBOOK_REGISTER_BASE = URLBASE + 'service/gradebook/'

    GBUUID = 'STELLAR:/project/testingstuff'
