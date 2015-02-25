#!/usr/bin/python
"""
 Python interface to Stellar Grade Book module

 Defines the class StellarGradeBook
"""

import csv
import json
import logging
import time

import requests


log = logging.getLogger(__name__)  # pylint: disable=C0103


class StellarGradeBook(object):
    """
    Python class representing interface to Stellar gradebook.

    Example usage:

    sg = StellarGradeBook('ichuang-cert.pem')
    ats = sg.get('academicterms')
    tc = ats['data'][0]['termCode']
    sg.get('academicterm',termCode=tc)

    students = sg.get_students()
    assignments = sg.get_assignments()
    sg.create_assignment('midterm1', 'mid1', 1.0, 100.0, '11-04-2013')

    sid, student = sg.get_student_by_email(email)
    aid, assignment = sg.get_assignment_by_name('midterm1')
    sg.set_grade(aid, sid, 95.2)

    sg.spreadsheet2gradebook(datafn)

    """

    GETS = {'academicterms': '',
            'academicterm': '/{termCode}',
            'gradebook': '?uuid={uuid}'}

    GBUUID = 'STELLAR:/project/mitxdemosite'
    TIMEOUT = 200  # connection timeout, seconds

    verbose = True
    gradebookid = None

    def __init__(
            self,
            cert,
            urlbase='https://learning-modules.mit.edu:8443/service/gradebook',
            gbuuid=None
    ):
        """
        Initialize StellarGradeBook instance.

          - urlbase:    URL base for gradebook API
            (still needs certs); default False
          - gbuuid:     gradebook UUID (eg STELLAR:/project/mitxdemosite)

        """
        # pem with private and public key application certificate for access
        self.cert = cert

        self.urlbase = urlbase
        self.ses = requests.Session()
        self.ses.cert = cert
        self.ses.timeout = self.TIMEOUT  # connection timeout
        self.ses.verify = True  # verify site certificate

        log.debug("------------------------------------------------------")
        log.info("[StellarGradeBook] init base=%s", urlbase)

        if gbuuid is not None:
            self.gradebookid = self.get_gradebook_id(gbuuid)

    def rest_action(self, func, url, **kwargs):
        """Routine to do low-level REST operation, with retry"""
        cnt = 1
        while cnt < 10:
            cnt += 1
            try:
                return self.rest_action_actual(func, url, **kwargs)
            except requests.ConnectionError, err:
                log.error(
                    "[StellarGradeBook] Error - connection error in "
                    "rest_action, err=%s", err
                )
                log.info("                   Retrying...")
            except requests.Timeout, err:
                log.exception(
                    "[StellarGradeBook] Error - timeout in "
                    "rest_action, err=%s", err
                )
                log.info("                   Retrying...")
        raise Exception(
            "[StellarGradeBook] rest_action failure: exceed max retries"
        )

    def rest_action_actual(self, func, url, **kwargs):
        """Routine to do low-level REST operation"""
        log.info('Running request to %s', url)
        resp = func(url, timeout=self.TIMEOUT, verify=False, **kwargs)
        try:
            retdat = json.loads(resp.content)
        except Exception:
            log.exception(resp.content)
            raise
        return retdat

    def get(self, service, params=None, **kwargs):
        """
        Generic GET operation for retrieving data from Gradebook API
        Example:
          sg.get('students/{gradebookId}', params=params, gradebookId=gbid)
        """
        urlfmt = '{base}/' + service + self.GETS.get(service, '')
        url = urlfmt.format(base=self.urlbase, **kwargs)
        if params is None:
            params = {}
        return self.rest_action(self.ses.get, url, params=params)

    def post(self, service, data, **kwargs):
        """
        Generic POST operation for sending data to Gradebook API.
        data should be a JSON string or a dict.  If it is not a string,
        it is turned into a JSON string for the POST body.
        """
        urlfmt = '{base}/' + service
        url = urlfmt.format(base=self.urlbase, **kwargs)
        if not (type(data) == str or type(data) == unicode):
            data = json.dumps(data)
        headers = {'content-type': 'application/json'}
        return self.rest_action(self.ses.post, url, data=data, headers=headers)

    def delete(self, service, data, **kwargs):
        """
        Generic DELETE operation for Gradebook API.
        """
        urlfmt = '{base}/' + service
        url = urlfmt.format(base=self.urlbase, **kwargs)
        if not (type(data) == str or type(data) == unicode):
            data = json.dumps(data)
        headers = {'content-type': 'application/json'}
        return self.rest_action(
            self.ses.delete, url, data=data, headers=headers
        )

    def get_gradebook_id(self, gbuuid):
        """return gradebookid for a given gradebook uuid."""
        gradebook_id = self.get('gradebook', uuid=gbuuid)
        if 'data' not in gradebook_id:
            log.info(gradebook_id)
            msg = "[StellarGradeBook] error in get_gradebook_id - no data"
            log.info(msg)
            raise Exception(msg)
        return gradebook_id['data']['gradebookId']

    def get_students(self, gradebookid='', simple=False, section_name=''):
        """
        return list of students for a given gradebook,
        specified by a gradebookid.
        example return list element:
        {
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
        }
        """
        params = dict(includePhoto='false', includeGradeInfo='false',
                      includeGradeHistory='false', includeMakeupGrades='false')

        url = 'students/{gradebookId}'
        if section_name:
            groupid, _ = self.get_section_by_name(section_name)
            if groupid is None:
                msg = (
                    'in get_students -- Error: '
                    'No such section %s' % section_name
                )
                log.critical(msg)
                raise Exception(msg)
            url += '/section/%s' % groupid

        sdat = self.get(
            url,
            params=params,
            gradebookId=gradebookid or self.gradebookid
        )

        if simple:
            # just return dict with keys email, name, section
            student_map = dict(
                accountEmail='email',
                displayName='name',
                section='section'
            )

            def remap(students):
                """ make email domain name uppercase
                """
                newx = dict((student_map[k], students[k]) for k in student_map)
                # match certs
                newx['email'] = newx['email'].replace('@mit.edu', '@MIT.EDU')
                return newx

            return [remap(x) for x in sdat['data']]

        return sdat['data']

    def get_section_by_name(self, section_name):
        """
        return section for a given section name
        :param section_name:
        :return: section
        """
        sections = self.get_sections()
        for sec in sections:
            if sec['name'] == section_name:
                return sec['groupId'], sec
        return None, None

    def get_sections(self, gradebookid='', simple=False):
        """
        return list of sections for a given gradebook,
        specified by a gradebookid.
        sample return:
        [
          {
            "name": "Unassigned",
            "editable": false,
            "members": null,
            "shortName": "def",
            "staffs": null,
            "groupId": 1293925
          }
        ]
        """
        params = dict(includeMembers='false')

        sdat = self.get(
            'sections/{gradebookId}',
            params=params,
            gradebookId=gradebookid or self.gradebookid
        )

        if simple:
            return [{'SectionName': x['name']} for x in sdat['data']]
        return sdat['data']

    def get_assignments(self, gradebookid='', simple=False):
        """
        return list of assignments for a given gradebook,
        specified by a gradebookid.
        """
        params = dict(includeMaxPoints='true',
                      includeAvgStats='false',
                      includeGradingStats='false')

        dat = self.get(
            'assignments/{gradebookId}',
            params=params, gradebookId=gradebookid or self.gradebookid
        )
        if simple:
            return [{'AssignmentName': x['name']} for x in dat['data']]
        return dat['data']

    def create_assignment(
            self, name, shortname, weight,
            maxpoints, duedatestr, gradebookid='',
            **kwargs
    ):  # pylint: disable=too-many-arguments
        """
        Create a new assignment.
        """
        data = {"name": name,
                "shortName": shortname,
                "weight": weight,
                'graderVisible': False,
                'gradingSchemeType': "NUMERIC",
                "gradebookId": gradebookid or self.gradebookid,
                "maxPointsTotal": maxpoints,
                "dueDateString": duedatestr}
        data.update(kwargs)
        log.info("[StellaGradeBook] Creating assignment %s", name)
        ret = self.post('assignment', data)
        log.debug('posted value=%s', ret)
        return ret

    def delete_assignment(self, aid):
        """
        Delete assignment specified by assignmentId aid.
        """
        return self.delete(
            'assignment/{assignmentId}',
            data={}, assignmentId=aid
        )

    def get_assignment_by_name(self, assignment_name, assignments=None):
        """
        Get assignment by name; returns assignment ID value (numerical)
        and assignment dict.
        """
        if assignments is None:
            assignments = self.get_assignments()
        for assignment in assignments:
            if assignment['name'] == assignment_name:
                return assignment['assignmentId'], assignment
        return None, None

    def set_grade(
            self, assignmentid, studentid, gradeval, gradebookid='', **kwargs
    ):
        """
        Set numerical grade for student & assignment.

         - assignmentid = numerical ID for assignment
         - studentid    = numerical ID for student
         - gradeval     = numerical grade value
         - gradebookid  = numerical ID for gradebook (optional)
        """
        gradeinfo = {"studentId": studentid,
                     "assignmentId": assignmentid,
                     "mode": 2,
                     "comment": 'from MITx %s' % time.ctime(time.time()),
                     "numericGradeValue": str(gradeval)}
        gradeinfo.update(kwargs)
        log.info(
            "[StellarGradeBook] student %s set_grade=%s for assignment %s",
            studentid,
            gradeval,
            assignmentid)
        return self.post(
            'grades/{gradebookId}',
            data=gradeinfo,
            gradebookId=gradebookid or self.gradebookid
        )

    # todo.consider renaming this to set_multi_grades()
    def multi_grade(self, garray, gradebookid=''):
        """
        Set multiple grades for students.
        """
        return self.post('multiGrades/{gradebookId}', data=garray,
                         gradebookId=gradebookid or self.gradebookid)

    def get_student_by_email(self, email, students=None):
        """
        Get student based on email address.  Calls self.get_students
        to get list of all students, if not passed as the students
        argument.  Returns studentid, student dict, if found.

        return None, None if not found.
        """
        if students is None:
            students = self.get_students()

        email = email.lower()
        for student in students:
            if student['accountEmail'].lower() == email:
                return student['studentId'], student
        return None, None

    def spreadsheet2gradebook(self, datafn, email_field=None, single=False):
        """
        Upload grades from CSV format spreadsheet file into the
        Stellar gradebook.  The spreadsheet should have a column named
        "External email"; this will be used as the student's email
        address (for looking up and matching studentId).

        Columns ID,Username,Full Name,edX email,External email are otherwise
        disregarded.  All other columns are taken as assignments.

        datafn = filename of data file, or readable file object

        If create_assignments=True:
            missing assignments(ie not in gradebook)
        are created.

        If single=True then grades are transferred one at a time, slowly.

        If email_field is specified, then that
        field name is taken as the student's email.

        TODO: give specification for default assignment grade_max and due date?
        returns dict, dt-time-delta
        """
        non_assignment_fields = [
            'ID', 'Username', 'Full Name', 'edX email', 'External email'
        ]

        if email_field is not None:
            non_assignment_fields.append(email_field)
        else:
            email_field = 'External email'

        if not hasattr(datafn, 'read'):
            file_pointer = open(datafn)
        else:
            file_pointer = datafn
        creader = csv.DictReader(file_pointer, dialect='excel')

        if single:
            self._spreadsheet2gradebook_slow(
                creader, email_field, non_assignment_fields
            )
            resp = None
        else:
            resp = self._spreadsheet2gradebook_multi(
                creader, email_field, non_assignment_fields
            )

        return resp

    def _spreadsheet2gradebook_multi(  # pylint: disable=too-many-locals
            self, creader,
            email_field, non_assignment_fields
    ):
        """
        Helper function: Transfer grades from spreadsheet using
        multiGrades (multiple students at a time). We do this by
        creating a large array containing all grades to transfer, then
        make one call to the gradebook API.
        """
        assignments = self.get_assignments()
        students = self.get_students()
        assignment2id = {}
        garray = []
        for cdat in creader:
            email = cdat[email_field]
            sid, _ = self.get_student_by_email(email, students)
            if sid is None:
                log.warning(
                    'Error in spreadsheet2gradebook: cannot find '
                    'student id for email="%s"\n', email
                )
            for field in cdat.keys():
                if field in non_assignment_fields:
                    continue
                if field not in assignment2id:
                    aid, _ = self.get_assignment_by_name(
                        field, assignments=assignments
                    )
                    if aid is None:
                        name = field
                        shortname = field[0:3] + field[-2:]
                        log.info('calling create_assignment from multi')
                        resp = self.create_assignment(
                            name, shortname, 1.0, 100.0, '12-15-2013'
                        )
                        if (
                                not resp.get('data', '') or
                                'assignmentId' not in resp.get('data')
                        ):
                            log.warning(
                                'Failed to create assignment %s', name)
                            log.info(resp)
                            msg = (
                                "Error ! Failed to create assignment %s", name
                            )
                            log.critical(msg)
                            raise Exception(msg)
                        aid = resp['data']['assignmentId']
                    log.info("Assignment %s has Id=%s", field, aid)
                    assignment2id[field] = aid

                aid = assignment2id[field]
                is_successful = True
                try:
                    gradeval = float(cdat[field]) * 1.0
                except ValueError as err:
                    log.exception(
                        "Failed in converting grade for student %s,"
                        " cdat=%s, err=%s", sid, cdat, err)
                    is_successful = False
                if is_successful:
                    garray.append(
                        {"studentId": sid,
                         "assignmentId": aid,
                         "numericGradeValue": gradeval,
                         "mode": 2,
                         "isGradeApproved": False}
                    )
        log.info(
            'Data read from file, doing multiGrades API '
            'call (%d grades)', len(garray)
        )
        tstart = time.time()
        resp = self.multi_grade(garray)
        duration = time.time() - tstart
        log.info(
            'multiGrades API call done (%d bytes returned) '
            'dt=%6.2f seconds.', len(json.dumps(resp)), duration
        )
        return resp, duration

    def _spreadsheet2gradebook_slow(  # pylint: disable=too-many-locals
            self, creader,
            email_field, non_assignment_fields
    ):
        """
        Helper function: Transfer grades from spreadsheet one at a time
        """
        assignments = self.get_assignments()
        assignment2id = {}
        students = self.get_students()
        for cdat in creader:
            email = cdat[email_field]
            sid, _ = self.get_student_by_email(email, students)
            for field in cdat.keys():
                if field in non_assignment_fields:
                    continue
                if field not in assignment2id:
                    aid, _ = self.get_assignment_by_name(
                        field, assignments=assignments
                    )
                    if aid is None:
                        name = field
                        shortname = field[0:3] + field[-2:]
                        resp = self.create_assignment(
                            name, shortname, 1.0, 100.0, '12-15-2013'
                        )
                        if 'assignmentId' not in resp['data']:
                            log.info(resp)
                            msg = (
                                "Error ! Failed to create assignment %s" % name
                            )
                            log.error(msg)
                            raise Exception(msg)
                        aid = resp['data']['assignmentId']
                        log.info("Assignment %s has Id=%s", field, aid)
                    assignment2id[field] = aid

                aid = assignment2id[field]
                gradeval = float(cdat[field]) * 1.0
                log.info(
                    "--> Student %s assignment %s grade %s",
                    email, field, gradeval)
                self.set_grade(aid, sid, gradeval)
