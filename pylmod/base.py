"""
PyLmod Base class
"""
import json
import logging

import requests


log = logging.getLogger(__name__)


class Base():
    TIMEOUT = 200  # connection timeout, seconds
    MAX_RETRIES = 10  # max attempts to call service

    # todo.consider moving this to config file
    URLBASE = 'https://learning-modules.mit.edu:8443/service'

    GETS = {'academicterms': '',
            'academicterm': '/{termCode}',
            'gradebook': '?uuid={uuid}',
            }

    GBUUID = 'STELLAR:/project/mitxdemosite'

    verbose = True
    gradebookid = None

    def __init__(
        self, cert, urlbase=None
    ):
        """
        Initialize PyLmod instance.

          - urlbase:    URL base for gradebook API (defaults to self.URLBASE)
            (still needs certs); default False

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
        log.info("[PyLmod] init base=%s" % urlbase)

    def rest_action(self, fn, url, **kwargs):
        """Routine to do low-level REST operation, with retry"""
        cnt = 1
        while cnt < self.MAX_RETRIES:
            cnt += 1
            try:
                return self.rest_action_actual(fn, url, **kwargs)
            except requests.ConnectionError, err:
                log.error(
                    "[PyLmod] Error - connection error in "
                    "rest_action, err=%s" % err
                )
                log.info("                   Retrying...")
            except requests.Timeout, err:
                log.exception(
                    "[PyLmod] Error - timeout in "
                    "rest_action, err=%s" % err
                )
                log.info("                   Retrying...")
        raise Exception(
            "[PyLmod] rest_action failure: tried %d times" % self.MAX_RETRIES
        )

    def rest_action_actual(self, fn, url, **kwargs):
        """Routine to do low-level REST operation"""
        log.info('Running request to %s' % url)
        r = fn(url, timeout=self.TIMEOUT, verify=False, **kwargs)
        try:
            retdat = json.loads(r.content)
        except Exception, err:
            log.exception(r.content)
            raise err
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

