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
    # Required signature for httpretty callback
    # pylint: disable=unused-argument
    raise socket.timeout('timeout')


class TestBase(BaseTest):
    """
    Verify basic RESTful capability and error handling in the base class.
    """
    # Unit tests generally should do protected-accesses
    # pylint: disable=protected-access
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
        # Strip off base URL to make sure it comes back
        urlbase = self.URLBASE[:-1]
        test_base = Base(self.CERT, urlbase)
        self.assertEqual(test_base.urlbase, self.URLBASE)
        self.assertEqual(test_base._session.cert, self.CERT)
        self.assertIsNone(test_base.gradebookid)

    def test_data_to_json(self):
        """Verify that we convert python data to json"""
        data = dict(a='b')
        self.assertEqual(
            Base._data_to_json(data),
            json.dumps(data)
        )
        self.assertEqual('a', Base._data_to_json('a'))

    def test_url_format(self):
        """Verify url format does the right thing"""
        base = Base(self.CERT, self.URLBASE)
        service = 'assignment'
        self.assertEqual(
            '{0}{1}'.format(self.URLBASE, service),
            base._url_format(service)
        )
        self.assertTrue(type(base._url_format(service)), str)

    @httpretty.activate
    def test_rest_action_success(self):
        """Test the rest action"""
        payload = {'a': 'b'}
        self._register_uri(body=json.dumps(payload))
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base._session.get
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
        rest_function = test_base._session.get
        response = test_base.rest_action(rest_function, self.URLBASE)
        self.assertEqual(payload, response)

    @httpretty.activate
    def test_rest_action_timeout(self):
        """Test the rest timeout indefinitely"""
        self._register_uri(timeout=True)
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base._session.get
        with self.assertRaisesRegex(
            requests.ConnectionError,
            'Max retries exceeded with url'
        ):
            test_base.rest_action(rest_function, self.URLBASE)

    @httpretty.activate
    def test_rest_action_not_json(self):
        """Test the rest timeout indefinitely"""
        self._register_uri(body='stuff')
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base._session.get
        with self.assertRaises(ValueError):
            test_base.rest_action(rest_function, self.URLBASE)

    def test_rest_action_connection(self):
        """Test the rest timeout indefinitely"""
        # This will try to actually connect to an invalid service
        test_base = Base(self.CERT, self.URLBASE)
        rest_function = test_base._session.get
        with self.assertRaises(requests.ConnectionError):
            test_base.rest_action(rest_function, self.URLBASE)

    @httpretty.activate
    def test_get_success(self):
        """Verify that get works as expected"""
        service = 'notreal'
        data = dict(a='b')
        full_url = '{0}{1}'.format(self.URLBASE, service)
        # Using array here because httpretty auto arrays params
        params = dict(c=['d'])
        httpretty.register_uri(
            httpretty.GET,
            full_url,
            body=json.dumps(data),
        )
        test_base = Base(self.CERT, self.URLBASE)
        response_json = test_base.get(service, params=params)
        self.assertEqual(data, response_json)
        last_request = httpretty.last_request()
        self.assertEqual(last_request.querystring, params)

        # Now without params
        response_json = test_base.get(service)
        self.assertEqual(data, response_json)
        last_request = httpretty.last_request()
        self.assertEqual(last_request.querystring, {})

    def test_get_failure(self):
        """Verify we are raising properly if a get request fails."""
        test_base = Base(self.CERT, self.URLBASE)
        with self.assertRaises(requests.ConnectionError):
            test_base.get('pinto_beans')

    @httpretty.activate
    def test_post_success(self):
        """Verify that post works as expected."""
        service = 'supercool'
        full_url = '{0}{1}'.format(self.URLBASE, service)
        response = dict(a='b')
        post_data = {'a': 'b'}

        # Apparently the service always returns JSON, but this seems
        # like a really suspicious assumption.  I would really like to
        # verify it.
        httpretty.register_uri(
            httpretty.POST,
            full_url,
            body=json.dumps(response)
        )
        test_base = Base(self.CERT, self.URLBASE)
        response_json = test_base.post(service, data=post_data)
        self.assertEqual(response, response_json)
        last_request = httpretty.last_request()
        self.assertEqual(last_request.parsed_body, post_data)

    def test_post_failure(self):
        """Verify we are raising properly if a get request fails."""
        test_base = Base(self.CERT, self.URLBASE)
        with self.assertRaises(requests.ConnectionError):
            test_base.post('make-beans', json.dumps(dict(beans='pinto')))

    @httpretty.activate
    def test_delete_success(self):
        """Verify that delete works as expected."""
        service = 'supercool'
        full_url = '{0}{1}'.format(self.URLBASE, service)
        response = dict(a='b')

        # Apparently the service always returns JSON, but this seems
        # like a really suspicious assumption.  I would really like to
        # verify it.
        httpretty.register_uri(
            httpretty.DELETE,
            full_url,
            body=json.dumps(response)
        )
        test_base = Base(self.CERT, self.URLBASE)
        response_json = test_base.delete(service)
        self.assertEqual(response, response_json)

    def test_delete_failure(self):
        """Verify we are raising properly if a get request fails."""
        test_base = Base(self.CERT, self.URLBASE)
        with self.assertRaises(requests.ConnectionError):
            test_base.delete('my-special-beans')
