#!/usr/bin/python
"""
 Python interface to Stellar Grade Book module

 Defines the class StellarGradeBook
"""

import json
import logging
import requests


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
