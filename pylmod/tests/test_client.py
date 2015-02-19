"""
Test pylmod/test_client.py module
"""
import unittest

import httpretty
import semantic_version

import pylmod


class TestClient(unittest.TestCase):
    """
    Tests for client.py
    """

    def test_version(self):
        # Will raise ValueError if not a semantic version
        semantic_version.Version(pylmod.VERSION)

    @httpretty.activate
    def test_get_academicterms(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_assignment_by_name(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_assignments(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_gradebookid(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_grades(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_section_by_name(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_sections(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_student_by_email(self):
        raise NotImplementedError

    @httpretty.activate
    def test_get_students(self):
        raise NotImplementedError

    @httpretty.activate
    def test_create_assignment(self):
        raise NotImplementedError

    @httpretty.activate
    def test_delete_assignment(self):
        raise NotImplementedError

    @httpretty.activate
    def test_set_grade(self):
        raise NotImplementedError

    @httpretty.activate
    def test_set_multigrades(self):
        raise NotImplementedError


