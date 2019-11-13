
Upgrading or changing package dependencies
==========================================

``setup.py`` specifies acceptable constraints for package versions, which 
usually follow Semantic Versioning conventions. The ``requirements`` files
specify exact versions for consistency between development, CI, and deployments.

1. Delete out and recreate your virtualenv environment, or uninstall packages. (E.g. ``pip uninstall -r requirements.txt``, etc.)
2. Edit ``setup.py``, specifying acceptable version constraints. The ``dev`` group of ``extras_require`` is for development and unit testing.
3. ``pip install -e .``
4. ``pip freeze >> requirements.txt`` and edit ``requirements.txt`` to preserve the ``--index-url`` and ``-e .`` lines.
5. ``pip install -e .[dev] >> test_requirements.txt`` and edit the file as above.
6. ``pip install -e .[doc] >> doc_requirements.txt`` and edit the file as above.

Running Tests
=============

Use ``tox``:

.. code-block:: sh

    pip install -r test_requirements.txt
    tox
