"""
Python interface to MIT Learning Module
"""

import logging
from gradebook import GradeBook
from membership import Membership


log = logging.getLogger(__name__)


class Client(GradeBook, Membership):
    """
    Python class representing interface to MIT Learning Modules.

    Example usage:

    sg = Client('ichuang-cert.pem')
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

    def get_academic_terms(self):
        raise NotImplementedError

    def get_assignment_by_name(self, assignment_name, assignments=None):
        return GradeBook.get_assignment_by_name(assignment_name, assignments)

    def get_assignments(self, gradebookid='', simple=False):
        return GradeBook.get_assignments(gradebookid, simple)

    def get_gradebook_id(self, gbuuid):
        return GradeBook.get_gradebook_id(gbuuid)

    def get_grades(self):
        raise NotImplementedError

    def get_section_by_name(self, section_name):
        return GradeBook.get_section_by_name(section_name)

    def get_sections(self, gradebookid='', simple=False):
        return GradeBook.get_sections(gradebookid, simple)

    def get_student_by_email(self, email, students=None):
        return GradeBook.get_student_by_email(email, students)

    def get_students(self, gradebookid='', simple=False, section_name=''):
        return GradeBook.get_students(gradebookid, simple, section_name)

    def create_assignment(self, name, shortname, weight,
        maxpoints, duedatestr, gradebookid='',
        **kwargs):
        return GradeBook.create_assignment(name, shortname, weight, maxpoints,
                                           duedatestr, gradebookid, **kwargs)

    def delete_assignment(self, aid):
        return GradeBook.delete_assignment(aid)

    def set_grade(self, assignmentid, studentid, gradeval,
                  gradebookid='', **kwargs):
        return GradeBook.set_grade(assignmentid, studentid, gradeval,
                                   gradebookid, **kwargs)

    def multi_grade(self, garray, gradebookid=''):
        return GradeBook.multi_grade(garray, gradebookid)

    def spreadsheet2gradebook(
        self, datafn, create_assignments=True, email_field=None, single=False):
        return GradeBook.spreadsheet2gradebook(datafn, create_assignments,
                                               email_field, single)
