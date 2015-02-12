# -*- coding: utf-8 -*-
"""
Client classes and methods for PyLmod module
"""

import logging

log = logging.getLogger('pylmod.client')  # pylint: disable=invalid-name


class Client(object):
    def get_academic_terms(self):
        raise NotImplementedError

    def get_assignment_by_name(self):
        raise NotImplementedError

    def get_assignments(self):
        raise NotImplementedError

    def get_gradebook_id(self):
        raise NotImplementedError

    def get_grades(self):
        raise NotImplementedError

    def get_section_by_name(self):
        raise NotImplementedError

    def get_sections(self):
        raise NotImplementedError

    def get_student_by_email(self):
        raise NotImplementedError

    def get_students(self):
        raise NotImplementedError

    def create_assignment(self):
        raise NotImplementedError

    def delete_assignment(self):
        raise NotImplementedError

    def set_grade(self):
        raise NotImplementedError

    def set_multigrades(self):
        raise NotImplementedError



