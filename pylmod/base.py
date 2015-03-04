#!/usr/bin/python
"""
 Python interface to Stellar Grade Book module

 Defines the class StellarGradeBook
"""

import json
import logging
import requests
import time


log = logging.getLogger(__name__)  # pylint: disable=C0103


class Base(object):
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

    def get_gradebook_id(self, gbuuid):
        """return gradebookid for a given gradebook uuid."""
        gradebook_id = self.get('gradebook', uuid=gbuuid)
        if 'data' not in gradebook_id:
            log.info(gradebook_id)
            msg = "[StellarGradeBook] error in get_gradebook_id - no data"
            log.info(msg)
            raise Exception(msg)
        return gradebook_id['data']['gradebookId']

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

    def get_section_by_name(self, section_name):
        """
        return section for a given section name

        :param section_name:
        :return:
        """
        sections = self.get_sections()
        for sec in sections:
            if sec['name'] == section_name:
                return sec['groupId'], sec
        return None, None

    def _spreadsheet2gradebook_multi(  # pylint: disable=too-many-locals
            self, creader, email_field, non_assignment_fields
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
                                'Failed to create assignment %s', name
                            )
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
                successful = True
                try:
                    gradeval = float(cdat[field]) * 1.0
                except ValueError as err:
                    log.exception(
                        "Failed in converting grade for student %s"
                        ", cdat=%s, err=%s", sid, cdat, err
                    )
                    successful = False
                if successful:
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
            self, creader, email_field, non_assignment_fields
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
                    assignment_id, _ = self.get_assignment_by_name(
                        field, assignments=assignments
                    )
                    if assignment_id is None:
                        name = field
                        shortname = field[0:3] + field[-2:]
                        resp = self.create_assignment(
                            name, shortname, 1.0, 100.0, '12-15-2013'
                        )
                        if 'assignmentId' not in resp['data']:
                            log.info(resp)
                            msg = (
                                "Error ! Failed to create assignment %s", name
                            )
                            log.error(msg)
                            raise Exception(msg)
                        assignment_id = resp['data']['assignmentId']
                        log.info("Assignment %s has Id=%s",
                                 field, assignment_id
                                )
                    assignment2id[field] = assignment_id

                assignment_id = assignment2id[field]
                gradeval = float(cdat[field]) * 1.0
                log.info(
                    "--> Student %s assignment %s grade %s",
                    email, field, gradeval
                )
                self.set_grade(assignment_id, sid, gradeval)

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
