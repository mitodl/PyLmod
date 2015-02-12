#!/usr/bin/python
#
# Python interface to Stellar Grade Book module
#
# Defines the class StellarGradeBook

import csv
import json
import logging
import pickle
import time

from lxml.html.soupparser import fromstring as fromstring_bs
import requests


log = logging.getLogger(__name__)


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

    URLBASE = 'https://learning-modules.mit.edu:8443/service/gradebook'

    GETS = {'academicterms': '',
            'academicterm': '/{termCode}',
            'gradebook': '?uuid={uuid}',
    }

    GBUUID = 'STELLAR:/project/mitxdemosite'
    TIMEOUT = 200  # connection timeout, seconds

    verbose = True
    gradebookid = None

    def __init__(
        self, cert, urlbase=None, touchstone=False,
        cookies=None, gbuuid=None
    ):
        """
        Initialize StellarGradeBook instance.

          - urlbase:    URL base for gradebook API (defaults to self.URLBASE)
          - touchstone: True if touchstone authentication to be done
            (still needs certs); default False
          - cookies:    requests.CookieJar object to use (optional)
          - gbuuid:     gradebook UUID (eg STELLAR:/project/mitxdemosite)

        """
        # pem with private and public key application certificate for access
        self.cert = cert

        if urlbase is not None:
            self.URLBASE = urlbase
        self.ses = requests.Session()
        self.ses.cert = cert
        self.ses.timeout = self.TIMEOUT  # connection timeout
        self.ses.verify = True  # verify site certificate

        log.debug("------------------------------------------------------")
        log.info("[StellarGradeBook] init base=%s" % urlbase)

        if cookies is not None:
            if type(cookies) == str:
                self.load_cookies_from_file(cookies)
            else:
                self.ses.cookies = cookies
        self.do_touchstone = touchstone
        if touchstone and cookies is None:
            self.init_touchstone()
        if gbuuid is not None:
            self.gradebookid = self.get_gradebookid(gbuuid)

    def load_cookies_from_file(self, fn):
        """
        Load cookies from file, given filename; format is python
        pickle dump
        """
        try:
            self.ses.cookies = pickle.load(open(fn))
        except Exception:
            log.exception("[StellarGradeBook] Failed to load cookie "
                          "file %s, skipping." % fn)
        self.cookie_fn = fn

    def save_cookies_to_file(self, fn=None):
        """
        Save cookies to file, given filename; format is python pickle dump
        """
        if fn is None:
            fn = self.cookie_fn
        pickle.dump(self.ses.cookies, open(fn, 'w'))
        log.info("[StellarGradeBook] Saved cookies to file %s" % fn)

    def init_touchstone(self):
        """Initialize requests session by doing touchstone authentication"""
        log.info("Authenticating via touchstone + certificates")
        s = self.ses
        r = s.get(self.URLBASE + "/academicterms")
        form = fromstring_bs(r.content).find('.//form[@id="IdPList"]')
        if form is not None:
            act = form.get('action')
            url2 = 'https://wayf.mit.edu'
            s.post(
                url2 + act,
                data={'user_idp': 'https://idp.mit.edu/shibboleth',
                      'Select': 'Continue',
                      'duration': 'session', }
            )
        log.debug("    ...stage 1 ok")
        url3 = "https://idp.mit.edu:446/idp/Authn/Certificate"
        r3 = s.get(
            url3,
            data={'authn_type': 'certificate',
                  'login_certificate': 'Use Certificate - Go'}
        )
        try:
            x = fromstring_bs(r3.content)
            url4 = x.find('.//form').get('action')
        except Exception, err:
            log.exception(r3.content)
            raise

        data = {}
        for k in x.findall('.//input[@type="hidden"]'):
            data[k.get('name')] = k.get('value')
        log.debug("    ...stage 2 ok")

        # print "data = %s" % data

        r4 = s.post(url4, data=data)
        if '"message"' in r4.content:
            log.info("    Successfully authenticated.")
            if hasattr(self, 'cookie_fn'):
                # save cookies to file if filename was given
                self.save_cookies_to_file()
            return
        log.critical("Failed to authenticate")
        log.debug(r4.content)
        raise Exception(
            "[StellarGradeBook] failed to authenticate via touchstone"
        )

    def rest_action(self, fn, url, **kwargs):
        """Routine to do low-level REST operation, with retry"""
        cnt = 1
        while cnt < 10:
            cnt += 1
            try:
                return self.rest_action_actual(fn, url, **kwargs)
            except requests.ConnectionError, err:
                log.error(
                    "[StellarGradeBook] Error - connection error in "
                    "rest_action, err=%s" % err
                )
                log.info("                   Retrying...")
            except requests.Timeout, err:
                log.exception(
                    "[StellarGradeBook] Error - timeout in "
                    "rest_action, err=%s" % err
                )
                log.info("                   Retrying...")
        raise Exception(
            "[StellarGradeBook] rest_action failure: exceed max retries"
        )

    def rest_action_actual(self, fn, url, **kwargs):
        """Routine to do low-level REST operation"""
        log.info('Running request to %s' % url)
        r = fn(url, timeout=self.TIMEOUT, verify=False, **kwargs)
        try:
            retdat = json.loads(r.content)
        except Exception, err:
            if (
                    self.do_touchstone and
                    ('<title>Touchstone@MIT' in r.content
                     or '<title>Account Provider Selection' in r.content)
            ):
                self.init_touchstone()
                return self.rest_action(fn, url, **kwargs)
            log.exception(r.content)
            raise
        return retdat

    def get(self, service, params=None, **kwargs):
        """
        Generic GET operation for retrieving data from Gradebook API
        Example:
          sg.get('students/{gradebookId}', params=params, gradebookId=gbid)
        """
        urlfmt = '{base}/' + service + self.GETS.get(service, '')
        url = urlfmt.format(base=self.URLBASE, **kwargs)
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
        url = urlfmt.format(base=self.URLBASE, **kwargs)
        if not (type(data) == str or type(data) == unicode):
            data = json.dumps(data)
        headers = {'content-type': 'application/json'}
        return self.rest_action(self.ses.post, url, data=data, headers=headers)

    def delete(self, service, data, **kwargs):
        """
        Generic DELETE operation for Gradebook API.
        """
        urlfmt = '{base}/' + service
        url = urlfmt.format(base=self.URLBASE, **kwargs)
        if not (type(data) == str or type(data) == unicode):
            data = json.dumps(data)
        headers = {'content-type': 'application/json'}
        return self.rest_action(
            self.ses.delete, url, data=data, headers=headers
        )

    def get_gradebookid(self, gbuuid):
        """return gradebookid for a given gradebook uuid."""
        gb = self.get('gradebook', uuid=gbuuid)
        if 'data' not in gb:
            log.info(gb)
            msg = "[StellarGradeBook] error in get_gradebookid - no data"
            log.info(msg)
            raise Exception(msg)
        return gb['data']['gradebookId']

    def get_students(self, gradebookid='', simple=False, sectionName=''):
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
        if sectionName:
            groupid, sec = self.get_section_by_name(sectionName)
            if groupid is None:
                msg = (
                    'in get_students -- Error: '
                    'No such section %s' % sectionName
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
            map = dict(
                accountEmail='email',
                displayName='name',
                section='section'
            )

            def remap(x):
                newx = dict((map[k], x[k]) for k in map)
                # match certs
                newx['email'] = newx['email'].replace('@mit.edu', '@MIT.EDU')
                return newx

            return [remap(x) for x in sdat['data']]

        return sdat['data']

    def get_section_by_name(self, sectionName):
        sections = self.get_sections()
        for sec in sections:
            if sec['name'] == sectionName:
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
    ):
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
        log.info("[StellaGradeBook] Creating assignment %s" % name)
        ret = self.post('assignment', data)
        log.debug('ret=%s' % ret)
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
        for a in assignments:
            if a['name'] == assignment_name:
                return a['assignmentId'], a
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
                     "numericGradeValue": str(gradeval),
        }
        gradeinfo.update(kwargs)
        log.info(
            "[StellarGradeBook] student %s set_grade=%s for assignment %s" %
            (studentid,
             gradeval,
             assignmentid))
        return self.post(
            'grades/{gradebookId}',
            data=gradeinfo,
            gradebookId=gradebookid or self.gradebookid
        )

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
        for s in students:
            if s['accountEmail'].lower() == email:
                return s['studentId'], s
        return None, None

    def spreadsheet2gradebook(
        self, datafn, create_assignments=True,
        email_field=None, single=False
    ):
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
        NonAssignmentFields = [
            'ID', 'Username', 'Full Name', 'edX email', 'External email'
        ]

        if email_field is not None:
            NonAssignmentFields.append(email_field)
        else:
            email_field = 'External email'

        if not hasattr(datafn, 'read'):
            fp = open(datafn)
        else:
            fp = datafn
        creader = csv.DictReader(fp, dialect='excel')

        if single:
            self._spreadsheet2gradebook_slow(
                creader, create_assignments, email_field, NonAssignmentFields
            )
            r = None
        else:
            r = self._spreadsheet2gradebook_multi(
                creader, create_assignments, email_field, NonAssignmentFields
            )

        return r

    def _spreadsheet2gradebook_multi(
        self, creader, create_assignments, email_field, NonAssignmentFields
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
            sid, student = self.get_student_by_email(email, students)
            if sid is None:
                log.warning(
                    'Error in spreadsheet2gradebook: cannot find '
                    'student id for email="%s"\n' % email
                )
            for field in cdat.keys():
                if field in NonAssignmentFields:
                    continue
                if field not in assignment2id:
                    aid, assignment = self.get_assignment_by_name(
                        field, assignments=assignments
                    )
                    if aid is None:
                        name = field
                        shortname = field[0:3] + field[-2:]
                        log.info('calling create_assignment from multi')
                        r = self.create_assignment(
                            name, shortname, 1.0, 100.0, '12-15-2013'
                        )
                        if (
                                not r.get('data', '') or
                                    'assignmentId' not in r.get('data')
                        ):
                            log.warning('Failed to create assignment %s' % name)
                            log.info(r)
                            msg = (
                                "Error ! Failed to create assignment %s" % name
                            )
                            log.critical(msg)
                            raise Exception(msg)
                        aid = r['data']['assignmentId']
                    log.info("Assignment %s has Id=%s" % (field, aid))
                    assignment2id[field] = aid

                aid = assignment2id[field]
                ok = True
                try:
                    gradeval = float(cdat[field]) * 1.0
                except Exception as err:
                    log.exception(
                        "Failed in converting grade for student %s"
                        ", cdat=%s, err=%s" % (sid, cdat, err)
                    )
                    ok = False
                if ok:
                    garray.append(
                        {"studentId": sid,
                         "assignmentId": aid,
                         "numericGradeValue": gradeval,
                         "mode": 2,
                         "isGradeApproved": False}
                    )
        log.info(
            'Data read from file, doing multiGrades API '
            'call (%d grades)' % len(garray)
        )
        tstart = time.time()
        r = self.multi_grade(garray)
        dt = time.time() - tstart
        log.info(
            'multiGrades API call done (%d bytes returned) '
            'dt=%6.2f seconds.' % (len(json.dumps(r)), dt)
        )
        return r, dt

    def _spreadsheet2gradebook_slow(
        self, creader, create_assignments, email_field, NonAssignmentFields
    ):
        """
        Helper function: Transfer grades from spreadsheet one at a time
        """
        assignments = self.get_assignments()
        assignment2id = {}
        students = self.get_students()
        for cdat in creader:
            email = cdat[email_field]
            sid, student = self.get_student_by_email(email, students)
            for field in cdat.keys():
                if field in NonAssignmentFields:
                    continue
                if field not in assignment2id:
                    aid, assignment = self.get_assignment_by_name(
                        field, assignments=assignments
                    )
                    if aid is None:
                        name = field
                        shortname = field[0:3] + field[-2:]
                        r = self.create_assignment(
                            name, shortname, 1.0, 100.0, '12-15-2013'
                        )
                        if 'assignmentId' not in r['data']:
                            log.info(r)
                            msg = (
                                "Error ! Failed to create assignment %s" % name
                            )
                            log.error(msg)
                            raise Exception(msg)
                        aid = r['data']['assignmentId']
                        log.info("Assignment %s has Id=%s" % (field, aid))
                    assignment2id[field] = aid

                aid = assignment2id[field]
                gradeval = float(cdat[field]) * 1.0
                log.info(
                    "--> Student %s assignment %s grade %s" % (
                        email, field, gradeval
                    )
                )
                r = self.set_grade(aid, sid, gradeval)
