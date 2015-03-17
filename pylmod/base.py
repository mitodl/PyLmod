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
    Base provides the transport for accessing the MIT Learning Modules (LMod).

    The Base class implements the functions that underlie the HTTP calls to
    the MIT Learning Modules (LMod) web service.  It shouldn't be
    instantiated directly as it is inherited by the classes that
    implement the API.

    Attributes:
        cert (unicode):
            file path to the certificate used to authenticate access
            to LMod web service
        urlbase (str):
            The URL of the LMod web service. i.e.
            learning-modules.mit.edu or learning-modules-test.mit.edu
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
        """Initialize Base instance.

        Args:
            cert (unicode):
                file path to the certificate used to authenticate access
                to LMod web service
            urlbase (str): URL base for gradebook API

         """
        # pem with private and public key application certificate for access
        self.cert = cert

        self.urlbase = urlbase
        if not urlbase.endswith('/'):
            self.urlbase += '/'
        self._session = requests.Session()
        self._session.cert = cert
        self._session.timeout = self.TIMEOUT  # connection timeout
        self._session.verify = True  # verify site certificate
        # Mount the retry adapter to the base url
        self._session.mount(urlbase, HTTPAdapter(max_retries=self.RETRIES))

        log.debug("------------------------------------------------------")
        log.info("[PyLmod] init urlbase=%s", urlbase)

    @staticmethod
    def _data_to_json(data):
        """Convert to json if it isn't already a string.

        Args:
            data (str): data to convert to json
        """
        if type(data) not in [str, unicode]:
            data = json.dumps(data)
        return data

    def _url_format(self, service):
        """Generate URL from urlbase and service.

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
        """Routine to do low-level REST operation, with retry.

        Args:
            func (callable): API function to call
            url (str): service URL endpoint
            kwargs (dict): addition parameters

        Raises:
            requests.RequestException
            ValueError

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
        """Generic GET operation for retrieving data from Learning Modules API.

        Args:
            service (str): The endpoint service to use, i.e. gradebook
            params (dict): additional parameters to add to the call

        Example:
          gbk.get('students/{gradebookId}', params=params, gradebookId=gbid)
        """
        url = self._url_format(service)
        if params is None:
            params = {}
        return self.rest_action(self._session.get, url, params=params)

    def post(self, service, data):
        """Generic POST operation for sending data to Learning Modules API.

        Data should be a JSON string or a dict.  If it is not a string,
        it is turned into a JSON string for the POST body.

        Args:
            service (str): The endpoint service to use, i.e. gradebook
            data (json or dict): the data payload

        """
        url = self._url_format(service)
        data = Base._data_to_json(data)
        # Add content-type for body in POST.
        headers = {'content-type': 'application/json'}
        return self.rest_action(self._session.post, url,
                                data=data, headers=headers)

    def delete(self, service):
        """Generic DELETE operation for Learning Modules API.

        Args:
            service (str): The endpoint service to use, i.e. gradebook

        """
        url = self._url_format(service)
        return self.rest_action(
            self._session.delete, url
        )
