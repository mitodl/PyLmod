# -*- coding: utf-8 -*-
"""
Testing of the module level stuff itself
"""
import unittest

import semantic_version


class TestModule(unittest.TestCase):
    """
    Test core module features, like asserting the version
    and making sure we are exposing our classes
    """

    def test_version(self):
        """
        Verify we have a valid semantic version
        """
        import pylmod
        semantic_version.Version(pylmod.__version__)

    def test_client_classes(self):
        """
        Assert that Client is available from the base module
        """
        import pylmod
        self.assertEqual(
            ['Client', 'GradeBook', 'Membership'],
            pylmod.__all__
        )
