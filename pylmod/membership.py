"""
Membership class
"""
import logging
from pylmod.base import Base

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Membership(Base):
    """
    Provide API for functions that return group membership data from MIT
    Learning Modules service.
    """

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
                """
                Convert mit.edu domain to upper-case for student emails

                :param students:
                :return:
                """
                newx = dict((student_map[k], students[k]) for k in student_map)
                # match certs
                newx['email'] = newx['email'].replace('@mit.edu', '@MIT.EDU')
                return newx

            return [remap(x) for x in sdat['data']]

        return sdat['data']
