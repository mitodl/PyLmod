Release Notes
=============

Release 0.2.0
-------------

- Manually updated version number in ``README.rst``.
- Updated setup.py for pytest version.
- Added normalize and max_pts cols to non_assignment_fields array.
- Made test requirements a list instead of a tuple with a list.
- Added support for max_pts and normalize columns in ``spreadsheet2gradebook``.
- Added tox, fixed test failure.
- Added autospec=``True`` to mock object creation.
- Added more membership test coverage.
- Made travis fixes.
- Added membership ``get_group`` and ``email_has_role``.
- Set maximum points to 1.0 on new assignments.
- Added additional debug logging while posting grades.
- Added get_staff() and get_options() to GradeBook.
- Added auto grade approval option
- Corrected the library to handle real ``get_section`` return data.

Release 0.1.0
-------------

- initial version
