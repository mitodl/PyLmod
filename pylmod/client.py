"""
Contains the Client class for pylmod that exposes all API classes.
"""
import logging
from pylmod.gradebook import GradeBook
from pylmod.membership import Membership

log = logging.getLogger(__name__)  # pylint: disable=C0103


class Client(GradeBook, Membership):  # pylint: disable=too-few-public-methods
    """Client class represents the interface to MIT Learning Modules API.

    Use Client class to incorporate multiple Learning Modules APIs.

    Example usage:

    .. code-block:: python

        gradebook = Client('ichuang-cert.pem')
        academic_terms = gradebook.get('academicterms')
        term_code = academic_terms['data'][0]['termCode']
        gradebook.get('academicterm',termCode=term_code)
        students = gradebook.get_students()
        assignments = gradebook.get_assignments()
        gradebook.create_assignment('midterm1', 'mid1', 1.0,
                                    100.0, '11-04-2013')
        student_id, student = gradebook.get_student_by_email(email)
        assignment_id, assignment =
            gradebook.get_assignment_by_name('midterm1')
        gradebook.set_grade(assignment_id, student_id, 95.2)
        gradebook.spreadsheet2gradebook(csv_file)
    """
    pass
