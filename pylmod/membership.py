"""
Contains Membership class
"""
import logging
from pylmod.exceptions import PyLmodUnexpectedData
from pylmod.base import Base

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Membership(Base):
    """Provide API for functions that return group membership data from
    MIT Learning Modules Web service.

    API reference at
    https://learning-modules-dev.mit.edu/service/membership/doc.html
    """
    def __init__(
            self,
            cert,
            urlbase='https://learning-modules.mit.edu:8443/',
            cuuid=None
    ):
        super(Membership, self).__init__(cert, urlbase)
        # Add service base
        self.urlbase += 'service/membership/'
        self.course_id = None
        if cuuid is not None:
            self.course_id = self.get_course_id(cuuid)

    def get_group(self, uuid=None):
        """Get group data based on uuid.

        Args:
            uuid (str): optional uuid, e.g. '/project/mitxdemosite'

        Raises:
            PyLmodUnexpectedData: No data was returned.
            requests.RequestException: Exception connection error

        Returns:
            dict: group json

        """
        if uuid is None:
            uuid = self.cuuid # so does course_id == group_id?
        group_data = self.get('group', params={'uuid':uuid})
        return group_data

    def get_group_id(self, uuid=None):
        """Get group id based on uuid.

        Args:
            uuid (str): optional uuid, e.g. '/project/mitxdemosite'

        Raises:
            PyLmodUnexpectedData: No group data was returned.
            requests.RequestException: Exception connection error

        Returns:
            int: numeric group id

        """
        group_data = self.get_group(uuid)
        try:
            return group_data['response']['docs'][0]['id']
        except KeyError, IndexError:
            failure_message = ('Error in get_group response data - '
                               'got {0}'.format(group_data))
            log.exception(failure_message)
            raise PyLmodUnexpectedData(failure_message)
        return None

    def get_membership(self, uuid=None):
        """Get membership data based on uuid.

        Args:
            uuid (str): optional uuid, e.g. '/project/mitxdemosite'

        Raises:
            PyLmodUnexpectedData: No data was returned.
            requests.RequestException: Exception connection error

        Returns:
            dict: membership json

        """
        group_id = self.get_group_id(uuid=uuid)
        uri = 'group/{group_id}/member'
        mbr_data = self.get(uri.format(group_id=group_id), params=None)
        return mbr_data

    def email_has_role(self, email, role_name, uuid=None):
        """Determine if an email is associated with a role.

        Args:
            email (str): user email
            role_name (str): user role, e.g. 'staff'
            uuid (str): optional uuid, e.g. '/project/mitxdemosite'

        Raises:
            PyLmodUnexpectedData: Unexpected data was returned.
            requests.RequestException: Exception connection error

        Returns:
            bool: True or False if email has role_name

        """
        mbr_data = self.get_membership(uuid=uuid)
        docs = []
        try:
            docs = mbr_data['response']['docs']
        except KeyError:
            failure_message = ('KeyError in membership data - '
                               'got {0}'.format(mbr_data))
            log.exception(failure_message)
            raise PyLmodUnexpectedData(failure_message)
        if len(docs) == 0:
            return False
        has_role = any(
            (x.get('email') == email and x.get('roleType') == role_name)
            for x in docs
        )
        if has_role:
            return True
        return False

    def get_course_id(self, course_uuid):
        """Get course id based on uuid.

        Args:
            uuid (str): course uuid, i.e. /project/mitxdemosite

        Raises:
            PyLmodUnexpectedData: No course data was returned.
            requests.RequestException: Exception connection error

        Returns:
            int: numeric course id

        """
        course_data = self.get(
            'courseguide/course?uuid={uuid}'.format(
                uuid=course_uuid or self.course_id
            ),
            params=None
        )
        try:
            return course_data['response']['docs'][0]['id']
        except KeyError:
            failure_message = ('KeyError in get_course_id - '
                               'got {0}'.format(course_data))
            log.exception(failure_message)
            raise PyLmodUnexpectedData(failure_message)
        except TypeError:
            failure_message = ('TypeError in get_course_id - '
                               'got {0}'.format(course_data))
            log.exception(failure_message)
            raise PyLmodUnexpectedData(failure_message)

    def get_course_guide_staff(self, course_id=''):
        """Get the staff roster for a course.

        Get a list of staff members for a given course,
        specified by a course id.

        Args:
            course_id (int): unique identifier for course, i.e. ``2314``

        Raises:
            requests.RequestException: Exception connection error
            ValueError: Unable to decode response content

        Returns:
            list: list of dictionaries containing staff data

            An example return value is:

            .. code-block:: python

                [
                    {
                        u'displayName': u'Huey Duck',
                        u'role': u'TA',
                        u'sortableDisplayName': u'Duck, Huey'
                    },
                    {
                        u'displayName': u'Louie Duck',
                        u'role': u'CourseAdmin',
                        u'sortableDisplayName': u'Duck, Louie'
                    },
                    {
                        u'displayName': u'Benjamin Franklin',
                        u'role': u'CourseAdmin',
                        u'sortableDisplayName': u'Franklin, Benjamin'
                    },
                    {
                        u'displayName': u'George Washington',
                        u'role': u'Instructor',
                        u'sortableDisplayName': u'Washington, George'
                    },
                ]
    """
        staff_data = self.get(
            'courseguide/course/{courseId}/staff'.format(
                courseId=course_id or self.course_id
            ),
            params=None
        )
        return staff_data['response']['docs']
