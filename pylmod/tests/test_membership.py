# -*- coding: utf-8 -*-
"""
Test the membership class
"""
import httpretty
import json
from mock import patch
from pylmod import Membership
from pylmod.exceptions import (
    PyLmodUnexpectedData,
)

from pylmod.tests.common import BaseTest


class TestMembership(BaseTest):
    """Validate defined methods and constructors in Membership class"""

    # Unit tests generally should do protected-accesses
    # pylint: disable=protected-access
    COURSE_ID = 12345
    ROLE = 'student'
    EMAIL = 'bigclass121@example.com'
    STAFF_BODY = {
        u'response':
        {
            u'docs':
            [
                {
                    u'displayName': u'Huey Duck',
                    u'role': u'TA',
                    u'sortableDisplayName': u'Duck, Huey'
                },
                {
                    u'displayName': u'Louie Duck',
                    u'role': u'CourseAdmin',
                    u'sortableDisplayName': u'Duck, Louie'
                },
                {
                    u'displayName': u'Benjamin Franklin',
                    u'role': u'CourseAdmin',
                    u'sortableDisplayName': u'Franklin, Benjamin'
                },
                {
                    u'displayName': u'George Washington',
                    u'role': u'Instructor',
                    u'sortableDisplayName': u'Washington, George'
                },
            ],
        },
    }

    COURSE_DATA = {
        u'response':
        {
            u'docs':
            [
                {
                    u'googleEnabled': True,
                    u'groupTemplate': u'project',
                    u'groupingScheme': None,
                    u'id': 12345,
                    u'longName': u'pylmod test Site',
                    u'name': u'pylmod test Site',
                    u'properties':
                    {
                        u'allowsStudentsToSwitchSection': u'1',
                        u'lastDateToSwitchSection': u'1480723199000'
                    },
                    u'termCode': u'2033FA',
                    u'uuid': u'/project/testingstuff'
                }
            ],
        },
    }

    MEMBERSHIP_DATA = {
        u'response': {
            u'docs':
            [
                {
                    "roleType": "student",
                    "email": "bigclass121@example.com",
                },
            ]
        }
    }

    def _register_get_course_id(self, body):
        """Handle API call to get course id"""
        httpretty.register_uri(
            httpretty.GET,
            '{0}courseguide/course?uuid={1}'.format(
                self.MEMBERSHIP_REGISTER_BASE,
                self.CUUID,
            ),
            body=json.dumps(body)
        )

    def _register_get_group(self, body):
        """Handle API call to get group"""
        httpretty.register_uri(
            httpretty.GET,
            '{0}group?uuid={1}'.format(
                self.MEMBERSHIP_REGISTER_BASE,
                self.CUUID,
            ),
            body=json.dumps(body),
        )

    def _register_get_membership(self, body):
        """Handle API call to get membership"""
        uri = '{0}group/{1}/member'.format(
            self.MEMBERSHIP_REGISTER_BASE,
            self.COURSE_DATA['response']['docs'][0]['id'],
        )
        httpretty.register_uri(
            httpretty.GET,
            uri,
            body=json.dumps(body),
        )

    def test_constructor(self):
        """Verify constructor does as expected i.e. append URLBASE with
        ``service/membership/``
        """
        # Strip off base URL to make sure it comes back
        urlbase = self.URLBASE[:-1]
        test_membership = Membership(self.CERT, uuid=None, urlbase=urlbase)
        self.assertEqual(
            test_membership.urlbase,
            self.URLBASE + 'service/membership/'
        )
        self.assertEqual(test_membership._session.cert, self.CERT)
        self.assertIsNone(test_membership.course_id)

    @httpretty.activate
    def test_constructor_with_cuuid(self):
        """Verify we can construct with CUUID and properly add
        self.course_id
        """
        self._register_get_course_id(body=self.COURSE_DATA)
        test_membership = Membership(self.CERT, self.URLBASE, self.CUUID)
        self.assertEqual(test_membership.course_id, self.COURSE_ID)

        # Also verify we made an API call
        last_request = httpretty.last_request()
        self.assertEqual(last_request.querystring, dict(uuid=[self.CUUID]))

    @httpretty.activate
    def test_get_course_guide_staff(self):
        """Verify that we can get staff roster as expected."""
        httpretty.register_uri(
            httpretty.GET,
            '{0}courseguide/course/{1}/staff'.format(
                self.MEMBERSHIP_REGISTER_BASE,
                self.COURSE_ID,
            ),
            body=json.dumps(self.STAFF_BODY)
        )
        test_membership = Membership(self.CERT, self.URLBASE)
        staff_list = test_membership.get_course_guide_staff(
            course_id=self.COURSE_ID
        )
        self.assertEqual(staff_list, self.STAFF_BODY['response']['docs'])

    @httpretty.activate
    @patch('pylmod.membership.log')
    def test_get_course_id(self, mock_log):
        """Verify that we can the course id by providing the course uuid."""
        self._register_get_course_id(body=self.COURSE_DATA)
        test_membership = Membership(self.CERT, self.URLBASE)
        course_id = test_membership.get_course_id(self.CUUID)
        self.assertEqual(course_id, self.COURSE_ID)

        # Produce KeyError and assert exception raised
        test_body = {'response': {'docs': {'enabled': True}}}
        self._register_get_course_id(test_body)
        with self.assertRaises(PyLmodUnexpectedData):
            test_membership.get_course_id(self.CUUID)
        mock_log.exception.assert_called_with(
            "KeyError in get_course_id - "
            "got {u'response': {u'docs': {u'enabled': True}}}"
        )

        # Produce TypeError and assert exception raised
        self._register_get_course_id(['arnold'])
        with self.assertRaises(PyLmodUnexpectedData):
            test_membership.get_course_id(self.CUUID)
        mock_log.exception.assert_called_with(
            "TypeError in get_course_id - got [u'arnold']"
        )

        # Remove data and assert exception raised
        test_body = {'nada': 'nothing'}
        self._register_get_course_id(test_body)
        with self.assertRaises(PyLmodUnexpectedData):
            test_membership.get_course_id(self.CUUID)

    @httpretty.activate
    def test_get_group(self):
        self._register_get_group(body=self.COURSE_DATA)
        test_membership = Membership(self.CERT, self.URLBASE)
        group_data = test_membership.get_group(self.CUUID)
        assert group_data == self.COURSE_DATA

    @httpretty.activate
    def test_get_group_id(self):
        self._register_get_group(body=self.COURSE_DATA)
        test_membership = Membership(self.CERT, self.URLBASE)
        group_id = test_membership.get_group_id(self.CUUID)
        assert group_id == self.COURSE_DATA['response']['docs'][0]['id']

    @httpretty.activate
    def test_get_membership(self):
        self._register_get_group(body=self.COURSE_DATA)
        self._register_get_membership(body=self.MEMBERSHIP_DATA)
        test_membership = Membership(self.CERT, self.URLBASE)
        mbr_data = test_membership.get_membership(self.CUUID)
        assert mbr_data == self.MEMBERSHIP_DATA

    @httpretty.activate
    def test_email_has_role(self):
        self._register_get_group(body=self.COURSE_DATA)
        self._register_get_membership(body=self.MEMBERSHIP_DATA)
        test_membership = Membership(self.CERT, self.URLBASE)
        has_role = test_membership.email_has_role(
            self.EMAIL, self.ROLE, uuid=self.CUUID
        )
        assert has_role is True
        has_role = test_membership.email_has_role(
            self.EMAIL, 'hacker', uuid=self.CUUID
        )
        assert has_role is False

    @httpretty.activate
    def test_get_group_default_uuid(self):
        self._register_get_group(body=self.COURSE_DATA)
        test_membership = Membership(self.CERT, self.URLBASE)
        group_data = test_membership.get_group()
        assert group_data == self.COURSE_DATA

    @httpretty.activate
    @patch('pylmod.membership.log')
    def test_get_group_id_errors(self, mock_log):
        test_membership = Membership(self.CERT, self.URLBASE)

        # IndexError
        test_body = {u'response': {u'docs': []}}
        self._register_get_group(body=test_body)
        with self.assertRaises(PyLmodUnexpectedData):
            test_membership.get_group_id(self.CUUID)
        mock_log.exception.assert_called_with(
            "Error in get_group response data - "
            "got {u'response': {u'docs': []}}"
        )

        # KeyError
        test_body = {u'response': {u'foo': []}}
        self._register_get_group(body=test_body)
        with self.assertRaises(PyLmodUnexpectedData):
            test_membership.get_group_id(self.CUUID)
        mock_log.exception.assert_called_with(
            "Error in get_group response data - "
            "got {u'response': {u'foo': []}}"
        )

    @httpretty.activate
    @patch('pylmod.membership.log')
    def test_email_has_role_errors(self, mock_log):
        test_membership = Membership(self.CERT, self.URLBASE)

        # KeyError
        test_body = {u'response': {u'foo': []}}
        self._register_get_group(body=self.COURSE_DATA)
        self._register_get_membership(body=test_body)
        with self.assertRaises(PyLmodUnexpectedData):
            test_membership.email_has_role(
                self.EMAIL, self.ROLE, uuid=self.CUUID
            )
        mock_log.exception.assert_called_with(
            "KeyError in membership data - "
            "got {u'response': {u'foo': []}}"
        )

    @httpretty.activate
    def test_email_has_role_docs(self):
        # len(docs) == 0
        test_body = {u'response': {u'docs': []}}
        self._register_get_group(body=self.COURSE_DATA)
        self._register_get_membership(body=test_body)
        test_membership = Membership(self.CERT, self.URLBASE)
        has_role = test_membership.email_has_role(
            self.EMAIL, self.ROLE, uuid=self.CUUID
        )
        assert has_role is False
