"""
    Python class representing interface to MIT Learning Modules web service.
"""

import json
import logging
import requests
from requests.adapters import HTTPAdapter


log = logging.getLogger(__name__)  # pylint: disable=C0103


class Base(object):
    """
    The Base class provides the transport for accessing MIT LMod web service.

    The Base class implements the functions that underlie the HTTP calls to
    the LMod web service.  It shouldn't be instantiated directly as it is
    inherited by the classes that implement the API.

    Attributes:
        cert: The certificate used to authenticate access to LMod web service
        urlbase: The URL of the LMod web service
    """
    GBUUID = 'STELLAR:/project/mitxdemosite'
    TIMEOUT = 200  # connection timeout, seconds
    RETRIES = 10  # Number of connection retries

    verbose = True
    gradebookid = None

    def __init__(
            self,
            cert,
            urlbase='https://learning-modules.mit.edu:8443/service/gradebook',
    ):
        """initialize Base instance

        Args:
            cert:
            urlbase:    URL base for gradebook API

         """
        # pem with private and public key application certificate for access
        self.cert = cert

        self.urlbase = urlbase
        if not urlbase.endswith('/'):
            self.urlbase += '/'
        self.ses = requests.Session()
        self.ses.cert = cert
        self.ses.timeout = self.TIMEOUT  # connection timeout
        self.ses.verify = True  # verify site certificate
        # Mount the retry adapter to the base url
        self.ses.mount(urlbase, HTTPAdapter(max_retries=self.RETRIES))

        log.debug("------------------------------------------------------")
        log.info("[PyLmod] init urlbase=%s", urlbase)

    @staticmethod
    def _data_to_json(data):
        """Convert to json if it isn't already a string

        Args:
            data:
        """
        if type(data) not in [str, unicode]:
            data = json.dumps(data)
        return data

    def _url_format(self, service):
        """Generate URL from urlbase, service

        Args:
            service (str): The endpoint service to use, i.e. gradebook

        Returns:
            str: URL to where the request should be made
        """
        base_service_url = '{base}{service}'.format(
            base=self.urlbase,
            service=service
        )
        return base_service_url

    def rest_action(self, func, url, **kwargs):
        """Routine to do low-level REST operation, with retry

        Args:
            func (str):
            url (str):

        """
        try:
            response = func(url, timeout=self.TIMEOUT, **kwargs)
        except requests.RequestException, err:
            log.exception(
                "[PyLmod] Error - connection error in "
                "rest_action, err=%s", err
            )
            raise err

        try:
            return response.json()
        except ValueError, err:
            log.exception('Unable to decode %s', response.content)
            raise err

    def get(self, service, params=None):
        """generic GET operation for retrieving data from Learning Modules API

        Args:
            service:
            params:

        Example:
          gbk.get('students/{gradebookId}', params=params, gradebookId=gbid)
        """
        url = self._url_format(service)
        if params is None:
            params = {}
        return self.rest_action(self.ses.get, url, params=params)

    def post(self, service, data):
        """generic POST operation for sending data to Learning Modules API.

        data should be a JSON string or a dict.  If it is not a string,
        it is turned into a JSON string for the POST body.

        Args:
            service:
            data:

        """
        url = self._url_format(service)
        data = Base._data_to_json(data)
        # Add content-type for body in POST.
        headers = {'content-type': 'application/json'}
        return self.rest_action(self.ses.post, url, data=data, headers=headers)

    def delete(self, service):
        """generic DELETE operation for Learning Modules API.

        Args:
            service:

        """
        url = self._url_format(service)
        return self.rest_action(
            self.ses.delete, url
        )
