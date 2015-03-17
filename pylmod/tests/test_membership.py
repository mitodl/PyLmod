# -*- coding: utf-8 -*-
"""
Test the membership class
"""
from pylmod import Membership
from pylmod.tests.common import BaseTest


class TestGradebook(BaseTest):
    """Validate defined methods and constructors in Membership class"""

    def test_constructor(self):
        """Verify constructor does as expected i.e. append URLBASE with
        ``service/membership/``
        """
        # Strip off base URL to make sure it comes back
        urlbase = self.URLBASE[:-1]
        test_membership = Membership(self.CERT, urlbase)
        self.assertEqual(
            test_membership.urlbase,
            self.URLBASE + 'service/membership/'
        )
        self.assertEqual(test_membership._session.cert, self.CERT)
        self.assertIsNone(test_membership.gradebookid)
