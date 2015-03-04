"""
GradeBook class
"""
import csv
import logging
import time
from pylmod.base import Base

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class GradeBook(Base):
    """
    Provide API for functions that return gradebook-related data from MIT
    Learning Modules service.
    """

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

    def create_assignment(  # pylint: disable=too-many-arguments
            self,
            name,
            shortname,
            weight,
            maxpoints,
            duedatestr,
            gradebookid='',
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
        log.info("[StellaGradeBook] Creating assignment %s", name)
        ret = self.post('assignment', data)
        log.debug('ret=%s', ret)
        return ret

    def delete_assignment(self, aid):
        """
        Delete assignment specified by assignmentId aid.
        """
        return self.delete(
            'assignment/{assignmentId}',
            data={}, assignmentId=aid
        )

    def set_grade(  # pylint: disable=too-many-arguments
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
            "[StellarGradeBook] student %s set_grade=%s for assignment %s",
            studentid,
            gradeval,
            assignmentid)
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

    def spreadsheet2gradebook(
            self, datafn, email_field=None, single=False
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

