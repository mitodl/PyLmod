"""
Common exception classes for pylmod
"""


class PyLmodException(Exception):
    """
    Base exception class for pylmod
    """
    pass


class PyLmodUnexpectedData(PyLmodException):
    """The data returned for the API wasn't as expected."""
    pass


class PyLmodFailedAssignmentCreation(PyLmodException):
    """Failed to create assignment"""
    pass


class PyLmodNoSuchSection(PyLmodException):
    """Failed to find the specified section"""
    pass
