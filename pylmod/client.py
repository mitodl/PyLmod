"""
Python interface to MIT Learning Modules service
"""
import logging
from pylmod.gradebook import GradeBook
from pylmod.membership import Membership

log = logging.getLogger(__name__)  # pylint: disable=C0103


class Client(GradeBook, Membership):  # pylint: disable=too-few-public-methods
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
    pass
