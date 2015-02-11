# -*- coding: utf-8 -*-
"""
Test pylmod/test_client.py module
"""
import unittest
import semantic_version


try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs
    import urllib

import pylmod


class TestClient(unittest.TestCase):
    """
    Tests for client.py
    """

    def test_version(self):
        # Will raise ValueError if not a semantic version
        semantic_version.Version(pylmod.VERSION)

