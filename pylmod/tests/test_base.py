"""
Test out the pylmod base class to verify authentication and RESTful verbs work.
"""
import json
import socket

import httpretty
import requests

from pylmod.base import Base
from pylmod.tests.common import BaseTest


def raise_timeout(request, uri, headers):
    """Raise a socket timeout during an httpretty call."""
    raise socket.timeout('timeout')


class TestBase(BaseTest):
    """
    Verify basic RESTful capability and error handling in the base class.
    """

    def _register_uri(self, body=None, responses=None, timeout=False):
        """Register base URI with responses and/or body"""

        if timeout:
            body = raise_timeout

        httpretty.register_uri(
            httpretty.GET,
            self.URLBASE,
            body=body,
            responses=responses
        )

    def test_constructor(self):
        """
        Verify the constructor converts all of our parameters into
        proper internal objects.
        """
        test_base = Base(self.CERT, self.URLBASE)
        self.assertEqual(test_base.urlbase, self.URLBASE)
        self.assertEqual(test_base.ses.cert, self.CERT)
        self.assertIsNone(test_base.gradebookid)

    @httpretty.activate
    def test_rest_action_success(self):
        """Test the rest action"""
        payload = {'a': 'b'}
        self._register_uri(body=json.dumps(payload))
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base.ses.get
        response = test_base.rest_action(rest_function, self.URLBASE)
        self.assertEqual(payload, response)

    @httpretty.activate
    def test_rest_action_success_eventually(self):
        """Wait some time and then succeed"""
        payload = {'a': 'b'}
        self._register_uri(
            responses=[
                httpretty.Response(body=raise_timeout),
                httpretty.Response(body=raise_timeout),
                httpretty.Response(body=json.dumps(payload)),
            ]
        )
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base.ses.get
        response = test_base.rest_action(rest_function, self.URLBASE)
        self.assertEqual(payload, response)

    @httpretty.activate
    def test_rest_action_timeout(self):
        """Test the rest timeout indefinitely"""
        self._register_uri(timeout=True)
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base.ses.get
        with self.assertRaisesRegexp(
                requests.ConnectionError,
                'Max retries exceeded with url'
        ):
            test_base.rest_action(rest_function, self.URLBASE)

    @httpretty.activate
    def test_rest_action_not_json(self):
        """Test the rest timeout indefinitely"""
        self._register_uri(body='stuff')
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base.ses.get
        with self.assertRaises(ValueError):
            test_base.rest_action(rest_function, self.URLBASE)

    def test_rest_action_connection(self):
        """Test the rest timeout indefinitely"""
        # This will try to actually connect to an invalid service
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base.ses.get
        with self.assertRaises(requests.ConnectionError):
            test_base.rest_action(rest_function, self.URLBASE)
