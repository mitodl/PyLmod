"""
Base class and common constants needed for pylmod tests
"""
import os
from unittest import TestCase


class BaseTest(TestCase):
    """
    Base class with convenient constants and URL endpoints for pylmod testing.
    """
    DATA_ROOT = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'data'
    )

    CERT = os.path.join(DATA_ROOT, 'certs', 'test_cert.pem')

    URLBASE = 'https://testingstuff/'

    GBUUID = 'STELLAR:/project/testingstuff'
