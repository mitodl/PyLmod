"""
    Python class representing interface to MIT Learning Modules web service.
"""

import json
import logging
import requests


log = logging.getLogger(__name__)  # pylint: disable=C0103


class Base(object):
    """
    The Base class provides the transport for accessing MIT LM web service.

    The Base class implements the functions that underlie the HTTP calls to
    the LM web service.  It shouldn't be instantiated directly as it is
    inherited by the classes that implement the API.

    Attributes:
        cert: The certificate used to authenticate access to LM web service
        urlbase: The URL of the LM web service
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
    ):
        """
        Initialize Base instance.

          - urlbase:    URL base for gradebook API
            (still needs certs); default False
         """
        # pem with private and public key application certificate for access
        self.cert = cert

        self.urlbase = urlbase
        self.ses = requests.Session()
        self.ses.cert = cert
        self.ses.timeout = self.TIMEOUT  # connection timeout
        self.ses.verify = True  # verify site certificate

        log.debug("------------------------------------------------------")
        log.info("[PyLmod] init base=%s", urlbase)

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
        Generic GET operation for retrieving data from Learning Modules API
        Example:
          gbk.get('students/{gradebookId}', params=params, gradebookId=gbid)
        """
        urlfmt = '{base}/' + service + self.GETS.get(service, '')
        url = urlfmt.format(base=self.urlbase, **kwargs)
        if params is None:
            params = {}
        return self.rest_action(self.ses.get, url, params=params)

    def post(self, service, data, **kwargs):
        """
        Generic POST operation for sending data to Learning Modules API.
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
        Generic DELETE operation for Learning Modules API.
        """
        urlfmt = '{base}/' + service
        url = urlfmt.format(base=self.urlbase, **kwargs)
        if not (type(data) == str or type(data) == unicode):
            data = json.dumps(data)
        headers = {'content-type': 'application/json'}
        return self.rest_action(
            self.ses.delete, url, data=data, headers=headers
        )
