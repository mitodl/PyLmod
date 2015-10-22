"""
Verify gradebook API calls with unit tests
"""
import json
import tempfile
import time

import httpretty
import mock

from pylmod import GradeBook
from pylmod.exceptions import (
    PyLmodUnexpectedData,
    PyLmodNoSuchSection,
    PyLmodFailedAssignmentCreation,
)
from pylmod.tests.common import BaseTest


class TestGradebook(BaseTest):
    """Validate defined gradebook methods in GradeBook class
    """
    # Unit tests generally should do protected-accesses
    # pylint: disable=protected-access
    GRADEBOOK_ID = 1234

    ASSIGNMENT_BODY = {
        u'data':
        [
            {
                u'assignmentId': 1,
                u'categoryId': 1293820,
                u'description': u'',
                u'dueDate': 1372392000000,
                u'dueDateString': u'06-28-2013',
                u'gradebookId': 1293808,
                u'graderVisible': True,
                u'gradingSchemeId': 2431243,
                u'gradingSchemeType': u'NUMERIC',
                u'isComposite': False,
                u'isHomework': False,
                u'maxPointsTotal': 10.0,
                u'name': u'Homework 1',
                u'shortName': u'HW1',
                u'userDeleted': False,
                u'weight': 1.0
            },
            {
                u'assignmentId': 2,
                u'categoryId': 1293820,
                u'description': u'',
                u'dueDate': 1383541200000,
                u'dueDateString': u'11-04-2013',
                u'gradebookId': 1293808,
                u'graderVisible': False,
                u'gradingSchemeId': 16708851,
                u'gradingSchemeType': u'NUMERIC',
                u'isComposite': False,
                u'isHomework': False,
                u'maxPointsTotal': 100.0,
                u'name': u'midterm1',
                u'shortName': u'mid1',
                u'userDeleted': False,
                u'weight': 1.0
            }
        ]
    }

    SECTION_BODY = {
        'data':
        {
            'recitation': [
                {
                    "name": "Unassigned",
                    "editable": False,
                    "members": None,
                    "shortName": "def",
                    "staffs": None,
                    "groupId": 1293925
                },
                {
                    "name": "Section 1",
                    "editable": False,
                    "members": None,
                    "shortName": "def",
                    "staffs": None,
                    "groupId": 123456
                },
            ]
        }
    }

    STUDENT_BODY = {
        'data':
        [
            {
                'accountEmail': 'a@example.com',
                'displayName': 'Alice',
                'section': 'Unassigned',
                'sectionId': 1293925,
                'studentId': 1,
            },
            {
                'accountEmail': 'b@mit.edu',
                'displayName': 'Bob',
                'section': 'Section 1',
                'sectionId': 123456,
                'studentId': 2,
            },
        ]
    }

    STAFF_BODY = {
        u'data':
        {
            u'COURSE_ADMIN':
            [
                {
                    u'accountEmail': u'lduck@mit.edu',
                    u'displayName': u'Louie Duck',
                },
            ],
            u'COURSE_TA':
            [
                {
                    u'accountEmail': u'benfranklin@mit.edu',
                    u'displayName': u'Benjamin Franklin',
                }
            ]
        },
    }

    SIMPLE_STAFF_BODY = [
        {
            u'accountEmail': u'lduck@mit.edu',
            u'displayName': u'Louie Duck',
            u'role': 'COURSE_ADMIN',
        },
        {
            u'accountEmail': u'benfranklin@mit.edu',
            u'displayName': u'Benjamin Franklin',
            u'role': 'COURSE_TA',
        }
    ]

    @staticmethod
    def _get_grades():
        """Return a dictionary list of grades.

        Since it has a dynamic time value these need to be generated
        with a function as close to the response time as possible.
        """
        return [
            {
                'studentId': 1,
                'assignmentId': 1,
                'mode': 2,
                'comment': 'from MITx {0}'.format(time.ctime(time.time())),
                'numericGradeValue': '1.1',
                'isGradeApproved': False
            },
            {
                'studentId': 2,
                'assignmentId': 1,
                'mode': 2,
                'comment': 'from MITx {0}'.format(time.ctime(time.time())),
                'numericGradeValue': '5.1',
                'isGradeApproved': False
            },
        ]

    def _get_multigrade(self, approve_grades=False):
        """Get a list of spreadsheet rows as dictionaries

        Get a list of spreadsheet row values to test submitting
        grades in a spreadsheet to the LMod web service.

        Args:
            approve_grades (boolean): list of spreadsheet rows as
                dictionaries

        Returns: list - list of spreadsheet rows

        """
        return [
                {'assignmentId': 1,
                 'isGradeApproved': approve_grades,
                 'mode': 2,
                 'numericGradeValue': 2.2,
                 'studentId': 1},
                {'assignmentId': 1,
                 'isGradeApproved': approve_grades,
                 'mode': 2,
                 'numericGradeValue': 1.1,
                 'studentId': None},
        ]

    def _register_get_gradebook(self, send_data=True):
        """Register gradebook endpoint for API."""
        body = {
            u"message": u"",
            u"status": 0,
            u"data":
            {
                u"gradebookId": self.GRADEBOOK_ID,
                u"uuid": self.GBUUID,
                u"courseName": u"Test",
                u"courseNumber": u"testingstuff",
                u"membershipSource": u"stellar",
                u"gradebookName": u"Gradebook for testingstuff"
            }
        }

        if not send_data:
            del body['data']
        httpretty.register_uri(
            httpretty.GET,
            '{0}gradebook'.format(self.GRADEBOOK_REGISTER_BASE),
            body=json.dumps(body)
        )

    def _register_get_options(self, send_data=True):
        """Handle get_options API call"""
        if send_data:
            body = json.dumps(
                {'data': {'membershipQualifier': '/project/mitxdemosite'}}
            )
        else:
            body = json.dumps({u'data': {u'nada': 'nothing'}})
        httpretty.register_uri(
            httpretty.GET,
            '{0}gradebook/options/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID
            ),
            body=body
        )

    def _register_get_assignments(self):
        """Respond to assignment list requests"""
        httpretty.register_uri(
            httpretty.GET,
            '{0}assignments/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID
            ),
            body=json.dumps(self.ASSIGNMENT_BODY)
        )

    def _register_create_assignment(self, body=''):
        """Handle assignment creation as needed"""
        httpretty.register_uri(
            httpretty.POST,
            '{0}assignment'.format(self.GRADEBOOK_REGISTER_BASE),
            body=json.dumps(body)
        )

    def _register_multi_grade(self, body=''):
        """Handle multigrade API call"""
        httpretty.register_uri(
            httpretty.POST,
            '{0}multiGrades/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE, self.GRADEBOOK_ID
            ),
            body=json.dumps(body)
        )

    def _register_get_sections(self):
        """Handle section getting API call"""
        httpretty.register_uri(
            httpretty.GET,
            '{0}sections/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID
            ),
            body=json.dumps(self.SECTION_BODY)
        )

    def _register_get_students(self):
        """Handle student getting API call"""
        httpretty.register_uri(
            httpretty.GET,
            '{0}students/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID
            ),
            body=json.dumps(self.STUDENT_BODY)
        )

    def _register_get_students_in_section(self):
        """Handle student getting API call"""
        section = self.SECTION_BODY['data']['recitation'][0]['groupId']
        students = [x for x in self.STUDENT_BODY['data']
                    if x['sectionId'] == section]
        students_data = dict(data=students)
        httpretty.register_uri(
            httpretty.GET,
            '{0}students/{1}/section/{2}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID,
                section,
            ),
            body=json.dumps(students_data)
        )

    def test_constructor(self):
        """Verify constructor does as expected without gbuuid (no remote API
        call).
        """
        # Strip off base URL to make sure it comes back
        urlbase = self.URLBASE[:-1]
        test_base = GradeBook(self.CERT, urlbase)
        self.assertEqual(
            test_base.urlbase,
            self.URLBASE + 'service/gradebook/'
        )
        self.assertEqual(test_base._session.cert, self.CERT)
        self.assertIsNone(test_base.gradebookid)

    @httpretty.activate
    def test_constructor_with_gbuuid(self):
        """Verify we can construct with GBUUID and properly add
        self.gradebook_id
        """
        self._register_get_gradebook()
        test_base = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        self.assertEqual(test_base.gradebook_id, self.GRADEBOOK_ID)

        # Also verify we made an API call
        last_request = httpretty.last_request()
        self.assertEqual(last_request.querystring, dict(uuid=[self.GBUUID]))

    @httpretty.activate
    def test_get_gradebook_id(self):
        """Verify get_gradebook_id works and sets the property as expected."""
        self._register_get_gradebook()
        test_gradebook = GradeBook(self.CERT, self.URLBASE)
        gradebook_id = test_gradebook.get_gradebook_id(self.GBUUID)
        self.assertEqual(gradebook_id, self.GRADEBOOK_ID)

        last_request = httpretty.last_request()
        self.assertEqual(last_request.querystring, dict(uuid=[self.GBUUID]))

        # Remove data and assert exception raised
        self._register_get_gradebook(False)
        with self.assertRaises(PyLmodUnexpectedData):
            test_gradebook.get_gradebook_id(self.GBUUID)

    @httpretty.activate
    def test_get_options(self):
        """Verify that we can get the options for a gradebook."""
        self._register_get_options(True)
        self._register_get_gradebook()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        options = gradebook.get_options(gradebook_id=self.GRADEBOOK_ID)
        self.assertIn('membershipQualifier', options)

        # check for no data
        self._register_get_options(False)
        options = gradebook.get_options(gradebook_id=self.GRADEBOOK_ID)
        self.assertNotIn('membershipQualifier', options)

    @httpretty.activate
    def test_get_assignments(self):
        """Verify we can get assignments as requested"""
        self._register_get_gradebook()
        self._register_get_assignments()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        assignments = gradebook.get_assignments()
        self.assertEqual(assignments, self.ASSIGNMENT_BODY['data'])
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.querystring,
            dict(
                includeMaxPoints=['true'],
                includeAvgStats=['false'],
                includeGradingStats=['false']
            )
        )

        # Check simple style
        assignments = gradebook.get_assignments(simple=True)
        self.assertEqual(
            assignments,
            [{'AssignmentName': x['name']}
             for x in self.ASSIGNMENT_BODY['data']]
        )

        # Verify parameter handling
        assignments = gradebook.get_assignments(
            max_points=False, avg_stats=True, grading_stats=True
        )
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.querystring,
            dict(
                includeMaxPoints=['false'],
                includeAvgStats=['true'],
                includeGradingStats=['true']
            )
        )

    @httpretty.activate
    def test_get_assignment_by_name(self):
        """Verify grabbing an assignment by name."""
        self._register_get_gradebook()
        # Verify just with a list (no API)
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        static_assignments = [dict(name='blah', assignmentId=1)]
        # No match
        self.assertEqual(
            (None, None),
            gradebook.get_assignment_by_name('stuff', static_assignments)
        )
        # Match
        self.assertEqual(
            (1, static_assignments[0]),
            gradebook.get_assignment_by_name(
                'blah', static_assignments
            )
        )

        # Verify we can get assignments via API and match
        self._register_get_assignments()
        assignment = self.ASSIGNMENT_BODY['data'][0]
        self.assertEqual(
            (assignment['assignmentId'], assignment),
            gradebook.get_assignment_by_name(assignment['name'])
        )

    @httpretty.activate
    def test_create_assignment(self):
        """Verify creating a new assignment."""
        response_data = {'message': 'success'}
        self._register_create_assignment(response_data)
        self._register_get_gradebook()

        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        response = gradebook.create_assignment(
            'Test Assign', 'test-assign', 1.0, 100.0, '11-04-2999'
        )
        self.assertEqual(response_data, response)

        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps({
                'name': 'Test Assign',
                'shortName': 'test-assign',
                'weight': 1.0,
                'graderVisible': False,
                'gradingSchemeType': 'NUMERIC',
                'gradebookId': self.GRADEBOOK_ID,
                'maxPointsTotal': 100.0,
                'dueDateString': '11-04-2999',
            })
        )

    @httpretty.activate
    def test_delete_assignment(self):
        """Verify deleting a new assignment."""
        response_data = {'message': 'success'}
        httpretty.register_uri(
            httpretty.DELETE,
            '{0}assignment/1'.format(self.GRADEBOOK_REGISTER_BASE),
            body=json.dumps(response_data)
        )
        self._register_get_gradebook()

        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        response = gradebook.delete_assignment(1)
        self.assertEqual(response_data, response)

    @httpretty.activate
    def test_set_grade(self):
        """Verify the setting of grades is as we expect.
        """
        response_data = {'message': 'success'}
        httpretty.register_uri(
            httpretty.POST,
            '{0}grades/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID
            ),
            body=json.dumps(response_data)
        )
        self._register_get_gradebook()

        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        grade = self._get_grades()[0]
        response = gradebook.set_grade(
            assignment_id=grade['assignmentId'],
            student_id=grade['studentId'],
            grade_value=grade['numericGradeValue'],
            isGradeApproved=False
        )
        self.assertEqual(response_data, response)
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(grade)
        )

    @httpretty.activate
    def test_multi_grade(self):
        """Verify that we can set multiple grades at once
        """
        response_data = {'message': 'success'}
        self._register_multi_grade(response_data)
        self._register_get_gradebook()

        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        grades = self._get_grades()
        response = gradebook.multi_grade(grades)
        self.assertEqual(response_data, response)
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(grades)
        )

    @httpretty.activate
    def test_get_sections(self):
        """Verify we can get sections for a course."""
        self._register_get_gradebook()
        self._register_get_sections()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        sections = gradebook.get_sections()
        self.assertEqual(sections, self.SECTION_BODY['data'])

        # Check simple style
        sections = gradebook.get_sections(simple=True)
        expected_sections = gradebook.unravel_sections(
            self.SECTION_BODY['data']
        )
        self.assertEqual(
            sections,
            [{'SectionName': x['name']}
             for x in expected_sections],
        )

    @httpretty.activate
    def test_get_staff(self):
        """Verify staff list is returned."""
        httpretty.register_uri(
            httpretty.GET,
            '{0}staff/{1}'.format(
                self.GRADEBOOK_REGISTER_BASE,
                self.GRADEBOOK_ID
            ),
            body=json.dumps(self.STAFF_BODY)
        )
        self._register_get_gradebook()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        staff = gradebook.get_staff(self.GRADEBOOK_ID)
        self.assertEqual(staff, self.STAFF_BODY['data'])

        # Check simple style
        staff = gradebook.get_staff(self.GRADEBOOK_ID, simple=True)
        expected_staff = gradebook.unravel_staff(self.STAFF_BODY)
        simple_list = []
        for member in expected_staff.__iter__():
            simple_list.append({
                'accountEmail': member['accountEmail'],
                'displayName': member['displayName'],
                'role': member['role'],
            })
        for member in staff:
            self.assertIn(member, simple_list)

    @httpretty.activate
    def test_get_section_by_name(self):
        """Verify grabbing a section by name."""
        self._register_get_gradebook()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)

        # With match
        self._register_get_sections()
        section_type = 'recitation'
        section = self.SECTION_BODY['data'][section_type][0]
        # Add the type modifier we now add to the structure
        section['sectionType'] = section_type
        self.assertEqual(
            (section['groupId'], section),
            gradebook.get_section_by_name(section['name'])
        )

        # Without match
        self._register_get_sections()
        section = 'Nope'
        self.assertEqual(
            (None, None),
            gradebook.get_section_by_name(section)
        )

    @httpretty.activate
    def test_get_students(self):
        """Verify being able to get students for section/gradebook."""
        self._register_get_gradebook()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        self._register_get_students()

        # Without section specified
        students = gradebook.get_students()
        self.assertEqual(students, self.STUDENT_BODY['data'])

        # Simple data return (and upcasing mit.edu)
        students = gradebook.get_students(simple=True)
        mapped_data = []
        for student in self.STUDENT_BODY['data']:
            email = student['accountEmail']
            if 'mit.edu' in email:
                email = email.replace('mit.edu', 'MIT.EDU')
            mapped_data.append(dict(
                email=email,
                name=student['displayName'],
                section=student['section'],
            ))
        self.assertEqual(mapped_data, students)

        # With valid section specified
        self._register_get_sections()
        self._register_get_students_in_section()
        section_name = self.SECTION_BODY['data']['recitation'][0]['name']
        students = gradebook.get_students(
            section_name=section_name
        )
        self.assertEqual(
            students,
            [x for x in self.STUDENT_BODY['data']
             if x['section'] == section_name]
        )

        # With invalid section
        with self.assertRaises(PyLmodNoSuchSection):
            students = gradebook.get_students(section_name='nope')

    @httpretty.activate
    def test_get_students_by_email(self):
        """Verify being able to get students by e-mail"""
        self._register_get_gradebook()
        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        self._register_get_students()

        real_student = self.STUDENT_BODY['data'][0]

        # Match against passed in list
        self.assertEqual(
            gradebook.get_student_by_email(
                real_student['accountEmail'],
                students=self.STUDENT_BODY['data']
            ),
            (real_student['studentId'], real_student)
        )

        # Get legitimate email
        student = gradebook.get_student_by_email(
            real_student['accountEmail']
        )
        self.assertEqual(student, (real_student['studentId'], real_student))

        # And with non-existent student
        self.assertEqual(
            (None, None),
            gradebook.get_student_by_email('cheese')
        )

    @httpretty.activate
    def test_spreadsheet2gradebook_multi(self):
        """Verify that we can use a spreadsheet to set grades
        """
        response_data = {'message': 'success'}
        self._register_get_gradebook()
        self._register_get_assignments()
        self._register_get_students()
        self._register_multi_grade(response_data)

        gradebook = GradeBook(self.CERT, self.URLBASE, self.GBUUID)
        # Create "spreadsheet" that doesn't require creating assignments.
        spreadsheet = [
            {'External email': 'a@example.com', 'Homework 1': 2.2},
            {'External email': 'cheese', 'Homework 1': 1.1},
        ]
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email'],
            approve_grades=False,
        )
        # Verify that we got the grades we expect
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(self._get_multigrade(approve_grades=False))
        )
        # Verify that we got the same grades, setting auto-approve = False
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email'],
            approve_grades=False
        )
        # Verify that we got the grades we expect
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(self._get_multigrade(approve_grades=False))
        )
        # Verify that we got the same grades, setting auto-approve = False
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email'],
            approve_grades=False
        )
        # Verify that we got the grades we expect
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(self._get_multigrade(approve_grades=False))
        )

        # Verify that we got the same grades, setting auto-approve = True
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email'],
            approve_grades=True
        )
        # Verify that we got the grades we expect
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(self._get_multigrade(approve_grades=True))
        )

        # Verify that we got the same grades, setting auto-approve = True
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email'],
            approve_grades=True
        )
        # Verify that we got the grades we expect
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps(self._get_multigrade(approve_grades=True))
        )

        # Now run it when the assignment doesn't exist to exercise
        # assignment creation code.

        # Setup create to return an assignment ID as expected by the API
        assignment_id = 3
        self._register_create_assignment(
            dict(data=dict(assignmentId=assignment_id))
        )
        spreadsheet = [
            {'External email': 'a@example.com', 'Homework 8': 2.2},
        ]
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email']
        )
        last_request = httpretty.last_request()
        expected_response = self._get_multigrade(approve_grades=False)[0]
        expected_response['assignmentId'] = assignment_id
        self.assertEqual(
            last_request.body,
            json.dumps([expected_response])
        )

        # Now with assignment failing to be created
        self._register_create_assignment({})
        with self.assertRaises(PyLmodFailedAssignmentCreation):
            gradebook._spreadsheet2gradebook_multi(
                csv_reader=spreadsheet,
                email_field='External email',
                non_assignment_fields=['External email'],
                approve_grades=False,
            )

        # And finally with a bad grade
        spreadsheet = [
            {'External email': 'a@example.com', 'Homework 1': 'foo'},
            {'External email': 'a@example.com', 'midterm1': 1.1},
        ]
        gradebook._spreadsheet2gradebook_multi(
            csv_reader=spreadsheet,
            email_field='External email',
            non_assignment_fields=['External email'],
            approve_grades=False
        )
        last_request = httpretty.last_request()
        self.assertEqual(
            last_request.body,
            json.dumps([
                {u'assignmentId': 2,
                 u'isGradeApproved': False,
                 u'mode': 2,
                 u'numericGradeValue': 1.1,
                 u'studentId': 1},
            ])
        )

    @mock.patch.object(
        GradeBook,
        '_spreadsheet2gradebook_multi',
        autospec=True,
    )
    @mock.patch('csv.DictReader')
    def test_spreadshee2gradebook(self, csv_patch, multi_patch):
        """Do a simple test of the spreadsheet to gradebook public method"""

        non_assignment_fields = [
            'ID', 'Username', 'Full Name', 'edX email', 'External email'
        ]
        email_field = 'External email'

        gradebook = GradeBook(self.CERT, self.URLBASE)
        # Test with tmp file handle
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            gradebook.spreadsheet2gradebook(temp_file.name)
            called_with = multi_patch.call_args
            assert csv_patch.call_count == 1
            self.assertEqual(called_with[0][2], email_field)
            self.assertEqual(called_with[0][3], non_assignment_fields)
        # Test with tmp file handle, approve_grades=False
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            gradebook.spreadsheet2gradebook(temp_file.name,
                                            approve_grades=False)
            called_with = multi_patch.call_args
            assert csv_patch.call_count == 2
            self.assertEqual(called_with[0][2], email_field)
            self.assertEqual(called_with[0][3], non_assignment_fields)
        # Test with tmp file handle, approve_grades=True
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            gradebook.spreadsheet2gradebook(temp_file.name,
                                            approve_grades=True)
            called_with = multi_patch.call_args
            assert csv_patch.call_count == 3
            self.assertEqual(called_with[0][2], email_field)
            self.assertEqual(called_with[0][3], non_assignment_fields)

        # Test with patched csvReader and named e-mail field
        alternate_email_field = 'stuff'
        gradebook.spreadsheet2gradebook(csv_patch, alternate_email_field)
        non_assignment_fields.append(alternate_email_field)
        called_with = multi_patch.call_args
        assert csv_patch.call_count == 4
        self.assertEqual(called_with[0][2], alternate_email_field)
        self.assertEqual(called_with[0][3], non_assignment_fields)
