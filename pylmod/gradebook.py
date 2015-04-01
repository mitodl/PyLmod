"""
Contains GradeBook class
"""
import csv
import json
import logging
import time

from pylmod.base import Base
from pylmod.exceptions import (
    PyLmodUnexpectedData,
    PyLmodFailedAssignmentCreation,
    PyLmodNoSuchSection,
)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class GradeBook(Base):
    """
    Since the MIT Learning Modules web service (LMod) usually returns
    response data,
    GradeBook API calls will return this data as a Python data structure,
    either a list or a dictionary. The data structure will often contain
    these items:

    - ``status`` - ``1`` = successful, ``-1`` = failed
    - ``message`` - details about any error condition, or success message
    - ``data`` - the returned data in a list or dictionary, if applicable

    For example, errors usually return a dictionary containing ``status``
    and ``message``.

    The response is in this format:

    .. code-block:: python

        {
            u'status':1,
            u'message':u'',
            u'data':{...}
        }

    API reference at
    https://learning-modules-dev.mit.edu/service/gradebook/doc.html
    """

    def __init__(
            self,
            cert,
            urlbase='https://learning-modules.mit.edu:8443/',
            gbuuid=None
    ):
        super(GradeBook, self).__init__(cert, urlbase)
        # Add service base
        self.urlbase += 'service/gradebook/'
        if gbuuid is not None:
            self.gradebook_id = self.get_gradebook_id(gbuuid)

    @staticmethod
    def unravel_sections(section_data):
        """Unravels section type dictionary into flat list of sections with
        type set as an attribute.

        Args:
            section_data(dict): Data return from py:method::get_sections

        Returns:
            list: Flat list of sections with ``sectionType`` set to
                type (i.e. recitation, lecture, etc)
        """
        sections = []
        for type, subsection_list in section_data.items():
            for section in subsection_list:
                section['sectionType'] = type
                sections.append(section)
        return sections

    def get_gradebook_id(self, gbuuid):
        """Return gradebookid for a given gradebook uuid.

        Args:
            gbuuid (str): gradebook uuid, i.e. ``STELLAR:/project/gbngtest``

        Raises:
            PyLmodUnexpectedData: No gradebook id returned
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content


        Returns:
            str: value of gradebook id
        """
        gradebook = self.get('gradebook', params={'uuid': gbuuid})
        if 'data' not in gradebook:
            failure_messsage = ('Error in get_gradebook_id '
                                'for {0} - no data'.format(
                                    gradebook
                                ))
            log.error(failure_messsage)
            raise PyLmodUnexpectedData(failure_messsage)
        return gradebook['data']['gradebookId']

    def get_assignments(
            self,
            gradebook_id='',
            simple=False,
            max_points=True,
            avg_stats=False,
            grading_stats=False
    ):
        """Get assignments for a gradebook.

        Return list of assignments for a given gradebook,
        specified by a py:attribute::gradebook_id.  You can control
        if additional parameters are returned, but the response
        time with py:attribute::avg_stats and py:attribute::grading_stats
        enabled is significantly longer.

        Args:
            gradebook_id (str): unique identifier for gradebook, i.e. ``2314``
            simple (bool): return just assignment names, default= ``False``
            max_points (bool):
                Max points is a property of the grading scheme for the
                assignment rather than a property of the assignment itself,
                default= ``True``
            avg_stats (bool): return average grade, default= ``False``
            grading_stats (bool):
                return grading statistics, i.e. number of approved grades,
                unapproved grades, etc., default= ``False``

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            list: list of assignment dictionaries

            An example return value is:

            .. code-block:: python

                [
                    {
                        u'assignmentId': 2431240,
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
                        u'assignmentId': 16708850,
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
                    },
                ]

       """
        # These are parameters required for the remote API call, so
        # there aren't too many arguments
        # pylint: disable=too-many-arguments
        params = dict(
            includeMaxPoints=json.dumps(max_points),
            includeAvgStats=json.dumps(avg_stats),
            includeGradingStats=json.dumps(grading_stats)
        )

        assignments = self.get(
            'assignments/{gradebookId}'.format(
                gradebookId=gradebook_id or self.gradebook_id
            ),
            params=params,
        )
        if simple:
            return [{'AssignmentName': x['name']}
                    for x in assignments['data']]
        return assignments['data']

    def get_assignment_by_name(self, assignment_name, assignments=None):
        """Get assignment by name.

        Get an assignment by name. It works by retrieving all assignments
        and returning the first assignment with a matching name. If the
        optional parameter ``assignments`` is provided, it uses this
        collection rather than retrieving all assignments from the service.

        Args:
            assignment_name (str): name of assignment
            assignments (dict): assignments to search, default: None
                When ``assignments`` is unspecified, all assignments
                are retrieved from the service.

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            tuple: tuple of assignment id and assignment dictionary

            .. code-block:: python

                (
                    16708850,
                    {
                        u'assignmentId': 16708850,
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
                )

        """
        if assignments is None:
            assignments = self.get_assignments()
        for assignment in assignments:
            if assignment['name'] == assignment_name:
                return assignment['assignmentId'], assignment
        return None, None

    def create_assignment(  # pylint: disable=too-many-arguments
            self,
            name,
            short_name,
            weight,
            max_points,
            due_date_str,
            gradebook_id='',
            **kwargs
    ):
        """Create a new assignment.

        Create a new assignment. By default, assignments are created
        under the `Uncategorized` category.

        Args:
            name (str): descriptive assignment name,
                i.e. ``new NUMERIC SIMPLE ASSIGNMENT``
            short_name (str): short name of assignment, one word of
                no more than 5 characters,  i.e. ``SAnew``
            weight (str): floating point value for weight, i.e. ``1.0``
            max_points (str): floating point value for maximum point
                total, i.e. ``100.0``
            due_date_str (str): due date as string in ``mm-dd-yyyy``
                format, i.e. ``08-21-2011``
            gradebook_id (str): unique identifier for gradebook, i.e. ``2314``
            kwargs (dict): dictionary containing additional parameters,
                i.e. ``graderVisible``, ``totalAverage``, and ``categoryId``.

                For example:

                .. code-block:: python

                    {
                        u'graderVisible': True,
                        u'totalAverage': None
                        u'categoryId': 1007964,
                    }

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            dict: dictionary containing ``data``, ``status`` and ``message``
                for example:

            .. code-block:: python

                {
                    u'data':
                    {
                        u'assignmentId': 18490492,
                        u'categoryId': 1293820,
                        u'description': u'',
                        u'dueDate': 1312171200000,
                        u'dueDateString': u'08-01-2011',
                        u'gradebookId': 1293808,
                        u'graderVisible': False,
                        u'gradingSchemeId': 18490493,
                        u'gradingSchemeType': u'NUMERIC',
                        u'isComposite': False,
                        u'isHomework': False,
                        u'maxPointsTotal': 100.0,
                        u'name': u'new NUMERIC SIMPLE ASSIGNMENT',
                        u'numStudentGradesToBeApproved': 0,
                        u'numStudentsToBeGraded': 614,
                        u'shortName': u'SAnew',
                        u'userDeleted': False,
                        u'weight': 1.0
                    },
                    u'message': u'assignment is created successfully',
                    u'status': 1
                }

        """
        data = {
            'name': name,
            'shortName': short_name,
            'weight': weight,
            'graderVisible': False,
            'gradingSchemeType': 'NUMERIC',
            'gradebookId': gradebook_id or self.gradebook_id,
            'maxPointsTotal': max_points,
            'dueDateString': due_date_str
        }
        data.update(kwargs)
        log.info("Creating assignment %s", name)
        response = self.post('assignment', data)
        log.debug('Received response data: %s', response)
        return response

    def delete_assignment(self, assignment_id):
        """Delete assignment.

        Delete assignment specified by assignment Id.

        Args:
            assignment_id (str): id of assignment to delete

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            dict: dictionary containing response ``status`` and ``message``

            .. code-block:: python

                {
                    u'message': u'assignment is deleted successfully',
                    u'status': 1
                }

        """
        return self.delete(
            'assignment/{assignmentId}'.format(assignmentId=assignment_id),
        )

    def set_grade(
            self,
            assignment_id,
            student_id,
            grade_value,
            gradebook_id='',
            **kwargs
    ):
        """Set numerical grade for student and assignment.

        Set a numerical grade for for a student and assignment. Additional
        options
        for grade ``mode`` are: OVERALL_GRADE = ``1``, REGULAR_GRADE = ``2``
        To set 'excused' as the grade, enter ``None`` for letter and
        numeric grade values,
        and pass ``x`` as the ``specialGradeValue``.
        ``ReturnAffectedValues`` flag determines whether or not to return
        student cumulative points and
        impacted assignment category grades (average and student grade).

        Args:
            assignment_id (str): numerical ID for assignment
            student_id (str): numerical ID for student
            grade_value (str): numerical grade value
            gradebook_id (str): unique identifier for gradebook, i.e. ``2314``
            kwargs (dict): dictionary of additional parameters

                .. code-block:: python

                    {
                        u'letterGradeValue':None,
                        u'booleanGradeValue':None,
                        u'specialGradeValue':None,
                        u'mode':2,
                        u'isGradeApproved':False,
                        u'comment':None,
                        u'returnAffectedValues': True,
                    }

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            dict: dictionary containing response ``status`` and ``message``

            .. code-block:: python

                {
                    u'message': u'grade saved successfully',
                    u'status': 1
                }

        """
        # pylint: disable=too-many-arguments

        # numericGradeValue stringified because 'x' is a possible
        # value for excused grades.
        grade_info = {
            'studentId': student_id,
            'assignmentId': assignment_id,
            'mode': 2,
            'comment': 'from MITx {0}'.format(time.ctime(time.time())),
            'numericGradeValue': str(grade_value)
        }
        grade_info.update(kwargs)
        log.info(
            "student %s set_grade=%s for assignment %s",
            student_id,
            grade_value,
            assignment_id)
        return self.post(
            'grades/{gradebookId}'.format(
                gradebookId=gradebook_id or self.gradebook_id
            ),
            data=grade_info,
        )

    def multi_grade(self, grade_array, gradebook_id=''):
        """Set multiple grades for students.

        Set multiple student grades for a gradebook.  The grades are passed
        as a list of dictionaries.

        Each grade dictionary in ``grade_array`` must contain a
        ``studentId`` and a ``assignmentId``.
        Options for grade mode are: OVERALL_GRADE = ``1``,
        REGULAR_GRADE = ``2``
        To set 'excused' as the grade, enter ``None`` for
        ``letterGradeValue`` and ``numericGradeValue``,
        and pass ``x`` as the ``specialGradeValue``.
        The ``ReturnAffectedValues`` flag determines whether to return
        student cumulative points and impacted assignment category
        grades (average and student grade)

        .. code-block:: python

            [
                {
                    u'comment': None,
                    u'booleanGradeValue': None,
                    u'studentId': 1135,
                    u'assignmentId': 4522,
                    u'specialGradeValue': None,
                    u'returnAffectedValues': True,
                    u'letterGradeValue': None,
                    u'mode': 2,
                    u'numericGradeValue': 50,
                    u'isGradeApproved': False
                },
                {
                    u'comment': None,
                    u'booleanGradeValue': None,
                    u'studentId': 1135,
                    u'assignmentId': 4522,
                    u'specialGradeValue': u'x',
                    u'returnAffectedValues': True,
                    u'letterGradeValue': None,
                    u'mode': 2,
                    u'numericGradeValue': None,
                    u'isGradeApproved': False
                },
                {
                    u'comment': None,
                    u'booleanGradeValue': None,
                    u'studentId': 1135,
                    u'assignmentId': None,
                    u'specialGradeValue': None,
                    u'returnAffectedValues': True,
                    u'letterGradeValue': u'A',
                    u'mode': 1,
                    u'numericGradeValue': None,
                    u'isGradeApproved': False
                }
            ]

        Args:
            grade_array (dict): an array of grades to save
            gradebook_id (str): unique identifier for gradebook, i.e. ``2314``

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            dict: dictionary containing response ``status`` and ``message``

        """
        return self.post(
            'multiGrades/{gradebookId}'.format(
                gradebookId=gradebook_id or self.gradebook_id
            ),
            data=grade_array,
        )

    def get_sections(self, gradebook_id='', simple=False):
        """Get the sections for a gradebook.

        Return a dictionary of types of sections containing a list of that
        type for a given gradebook.  Specified by a gradebookid.

        If simple=True, a list of dictionaries is provided for each
        section regardless of type. The dictionary only contains one
        key ``SectionName``.

        Args:
            gradebook_id (str): unique identifier for gradebook, i.e. ``2314``
            simple (bool): return a list of section names only

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            dict: Dictionary of section types where each type has a
                list of sections

            An example return value is:

            .. code-block:: python

                {
                    u'recitation':
                    [
                        {
                            u'editable': False,
                            u'groupId': 1293925,
                            u'groupingScheme': u'Recitation',
                            u'members': None,
                            u'name': u'Unassigned',
                            u'shortName': u'DefaultGroupNoCollisionPlease1234',
                            u'staffs': None
                        },
                        {
                            u'editable': True,
                            u'groupId': 1327565,
                            u'groupingScheme': u'Recitation',
                            u'members': None,
                            u'name': u'r01',
                            u'shortName': u'r01',
                            u'staffs': None},
                            {u'editable': True,
                            u'groupId': 1327555,
                            u'groupingScheme': u'Recitation',
                            u'members': None,
                            u'name': u'r02',
                            u'shortName': u'r02',
                            u'staffs': None
                        }
                    ]
                }

        """
        params = dict(includeMembers='false')

        section_data = self.get(
            'sections/{gradebookId}'.format(
                gradebookId=gradebook_id or self.gradebook_id
            ),
            params=params
        )

        if simple:
            sections = self.unravel_sections(section_data['data'])
            return [{'SectionName': x['name']} for x in sections]
        return section_data['data']

    def get_section_by_name(self, section_name):
        """Get a section by its name.

        Get a list of sections for a given gradebook,
        specified by a gradebookid.

        Args:
            section_name (str): The section's name.

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            tuple: tuple of group id, and section dictionary

            An example return value is:

            .. code-block:: python

                (
                    1327565,
                    {
                        u'editable': True,
                        u'groupId': 1327565,
                        u'groupingScheme': u'Recitation',
                        u'members': None,
                        u'name': u'r01',
                        u'shortName': u'r01',
                        u'staffs': None
                    }
                )

        """
        sections = self.unravel_sections(self.get_sections())
        for section in sections:
            if section['name'] == section_name:
                return section['groupId'], section
        return None, None

    def get_students(
            self,
            gradebook_id='',
            simple=False,
            section_name='',
            include_photo=False,
            include_grade_info=False,
            include_grade_history=False,
            include_makeup_grades=False
    ):
        """Get students for a gradebook.

        Get a list of students for a given gradebook,
        specified by a gradebook id. Does not include grade data.

        Args:
            gradebook_id (str): unique identifier for gradebook, i.e. ``2314``
            simple (bool):
                if ``True``, just return dictionary with keys ``email``,
                ``name``, ``section``, default = ``False``
            section_name (str): section name
            include_photo (bool): include student photo, default= ``False``
            include_grade_info (bool):
                include student's grade info, default= ``False``
            include_grade_history (bool):
                include student's grade history, default= ``False``
            include_makeup_grades (bool):
                include student's makeup grades, default= ``False``

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            list: list of student dictionaries

        .. code-block:: python

            [{
                u'accountEmail': u'stellar.test2@gmail.com',
                u'displayName': u'Molly Parker',
                u'photoUrl': None,
                u'middleName': None,
                u'section': u'Unassigned',
                u'sectionId': 1293925,
                u'editable': False,
                u'overallGradeInformation': None,
                u'studentId': 1145,
                u'studentAssignmentInfo': None,
                u'sortableName': u'Parker, Molly',
                u'surname': u'Parker',
                u'givenName': u'Molly',
                u'nickName': u'Molly',
                u'email': u'stellar.test2@gmail.com'
            },]

        """
        # These are parameters required for the remote API call, so
        # there aren't too many arguments, or too many variables
        # pylint: disable=too-many-arguments,too-many-locals

        # Set params by arguments
        params = dict(
            includePhoto=json.dumps(include_photo),
            includeGradeInfo=json.dumps(include_grade_info),
            includeGradeHistory=json.dumps(include_grade_history),
            includeMakeupGrades=json.dumps(include_makeup_grades),
        )

        url = 'students/{gradebookId}'
        if section_name:
            group_id, _ = self.get_section_by_name(section_name)
            if group_id is None:
                failure_message = (
                    'in get_students -- Error: '
                    'No such section %s' % section_name
                )
                log.critical(failure_message)
                raise PyLmodNoSuchSection(failure_message)
            url += '/section/{0}'.format(group_id)

        student_data = self.get(
            url.format(
                gradebookId=gradebook_id or self.gradebook_id
            ),
            params=params,
        )

        if simple:
            # just return dict with keys email, name, section
            student_map = dict(
                accountEmail='email',
                displayName='name',
                section='section'
            )

            def remap(students):
                """Convert mit.edu domain to upper-case for student emails.

                The mit.edu domain for user email must be upper-case,
                i.e. MIT.EDU.

                Args:
                    students (list): list of students

                Returns:
                    dict: dictionary of updated student email domains
                """
                newx = dict((student_map[k], students[k]) for k in student_map)
                # match certs
                newx['email'] = newx['email'].replace('@mit.edu', '@MIT.EDU')
                return newx

            return [remap(x) for x in student_data['data']]

        return student_data['data']

    def get_student_by_email(self, email, students=None):
        """Get a student based on an email address.

        Calls ``self.get_students()`` to get list of all students,
        if not passed as the ``students`` parameter.

        Args:
            email (str): student email
            students (dict): dictionary of students to search, default: None
                When ``students`` is unspecified, all students in gradebook
                are retrieved.

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            tuple: tuple of student id and student dictionary.
        """
        if students is None:
            students = self.get_students()

        email = email.lower()
        for student in students:
            if student['accountEmail'].lower() == email:
                return student['studentId'], student
        return None, None

    def _spreadsheet2gradebook_multi(
            self, csv_reader, email_field, non_assignment_fields
    ):
        """Transfer grades from spreadsheet to array.

        Helper function that transfer grades from spreadsheet using
        ``multi_grade()`` (multiple students at a time). We do this by
        creating a large array containing all grades to transfer, then
        make one call to the Gradebook API.

        Args:
            csv_reader (list): list of rows in CSV file
            email_field (str):
            non_assignment_fields (list):
                list of column names in CSV file that

        Raises:
            PyLmodFailedAssignmentCreation: Failed to create assignment
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            tuple: tuple of dictionary containing response ``status``
            and ``message``, and duration of operation

        """
        # pylint: disable=too-many-locals
        assignments = self.get_assignments()
        students = self.get_students()
        assignment2id = {}
        grade_array = []
        for row in csv_reader:
            email = row[email_field]
            sid, _ = self.get_student_by_email(email, students)
            if sid is None:
                log.warning(
                    'Error in spreadsheet2gradebook: cannot find '
                    'student id for email="%s"\n', email
                )
            for field in row.keys():
                if field in non_assignment_fields:
                    continue
                if field not in assignment2id:
                    assignment_id, _ = self.get_assignment_by_name(
                        field, assignments=assignments
                    )
                    # If no assignment found, try creating it.
                    if assignment_id is None:
                        name = field
                        shortname = field[0:3] + field[-2:]
                        log.info('calling create_assignment from multi')
                        response = self.create_assignment(
                            name, shortname, 1.0, 100.0, '12-15-2013'
                        )
                        if (
                                not response.get('data', '') or
                                'assignmentId' not in response.get('data')
                        ):
                            failure_message = (
                                "Error! Failed to create assignment {0}"
                                ", got {1}".format(
                                    name, response
                                )
                            )
                            log.critical(failure_message)
                            raise PyLmodFailedAssignmentCreation(
                                failure_message
                            )
                        assignment_id = response['data']['assignmentId']
                    log.info("Assignment %s has Id=%s", field, assignment_id)
                    assignment2id[field] = assignment_id

                assignment_id = assignment2id[field]
                successful = True
                try:
                    # Try to convert to numeric, but grade the
                    # rest anyway if any particular grade isn't a number
                    gradeval = float(row[field]) * 1.0
                except ValueError as err:
                    log.exception(
                        "Failed in converting grade for student %s"
                        ", row=%s, err=%s", sid, row, err
                    )
                    successful = False
                if successful:
                    grade_array.append({
                        "studentId": sid,
                        "assignmentId": assignment_id,
                        "numericGradeValue": gradeval,
                        "mode": 2,
                        "isGradeApproved": False
                    })
        # Everything is setup to post, do the post and track the time
        # it takes.
        log.info(
            'Data read from file, doing multiGrades API '
            'call (%d grades)', len(grade_array)
        )
        tstart = time.time()
        response = self.multi_grade(grade_array)
        duration = time.time() - tstart
        log.info(
            'multiGrades API call done (%d bytes returned) '
            'dt=%6.2f seconds.', len(json.dumps(response)), duration
        )
        return response, duration

    def spreadsheet2gradebook(
            self, csv_file, email_field=None,
    ):
        """Upload grade spreadsheet to gradebook.

        Upload grades from CSV format spreadsheet file into the
        Learning Modules gradebook.  The spreadsheet must have a column
        named ``External email`` which is used as the student's email
        address (for looking up and matching studentId).

        These columns are disregarded: ``ID``, ``Username``,
        ``Full Name``, ``edX email``, ``External email``.
        All other columns are taken as assignments.

        If ``email_field`` is specified, then that field name is taken as
        the student's email.

        .. code-block:: none

            External email,AB Assignment 01,AB Assignment 02
            jeannechiang@gmail.com,1.0,0.9
            stellar.test2@gmail.com,0.2,0.4
            stellar.test1@gmail.com,0.93,0.77

        Args:
            csv_reader (str): filename of csv data, or readable file object
            email_field (str): student's email

        Raises:
            PyLmodFailedAssignmentCreation: Failed to create assignment
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            tuple: tuple of dictionary containing response ``status``
            and ``message``, and duration of operation

        """
        non_assignment_fields = [
            'ID', 'Username', 'Full Name', 'edX email', 'External email'
        ]

        if email_field is not None:
            non_assignment_fields.append(email_field)
        else:
            email_field = 'External email'

        if not hasattr(csv_file, 'read'):
            file_pointer = open(csv_file)
        else:
            file_pointer = csv_file
        csv_reader = csv.DictReader(file_pointer, dialect='excel')

        response = self._spreadsheet2gradebook_multi(
            csv_reader, email_field, non_assignment_fields
        )
        return response
