"""
Contains the Client class for pylmod that exposes all API classes.
"""
import logging
from pylmod.gradebook import GradeBook
from pylmod.membership import Membership

log = logging.getLogger(__name__)  # pylint: disable=C0103


class Client(GradeBook, Membership):  # pylint: disable=too-few-public-methods
    """
    Python class representing interface to MIT Learning Modules API.

    Use Client class to incorporate multiple Learning Modules APIs.

    Example usage:
    gradebook = Client('ichuang-cert.pem')
    ats = gradebook.get('academicterms')
    tc = ats['data'][0]['termCode']
    gradebook.get('academicterm',termCode=tc)
    students = gradebook.get_students()
    assignments = gradebook.get_assignments()
    gradebook.create_assignment('midterm1', 'mid1', 1.0, 100.0, '11-04-2013')
    sid, student = gradebook.get_student_by_email(email)
    aid, assignment = gradebook.get_assignment_by_name('midterm1')
    gradebook.set_grade(aid, sid, 95.2)
    gradebook.spreadsheet2gradebook(datafn)
    """
    pass
