PyLmod
========
:PyLmod: Python implementation of MIT Learning Modules API
:Version: 0.1.0
:Author: MIT Office of Digital Learning
:Homepage: http://engineering.odl.mit.edu
:License: BSD

PyLmod provides a Python library to access the MIT Learning Modules web
service (described below). PyLmod was created to support
MIT's use of OpenedX for residential courses, but the library is open
source to enable easier access to that service for Python application
developers at MIT. PyLmod encapsulates the Learning Modules web service
making it more pythonic and easier to incorporate into Python applications.

The MIT Learning Modules web service, maintained by MIT Information
Systems and Technologies (IS&T), exposes an API to MIT systems of
record for classes, students, and grades. Its documentation for gradebook
and membership is available at these links.

Gradebook module
    `https://learning-modules-test.mit.edu/service/gradebook/doc.html
    <https://learning-modules-test.mit.edu/service/gradebook/doc.html>`_

Membership module
    `https://learning-modules-test.mit.edu/service/membership/doc.html
    <https://learning-modules-test.mit.edu/service/membership/doc.html>`_

Getting Started
===============
The Learning Modules web service requires authentication by x.509
certificates. You must create an application certificate and config
the Learning Modules web service to recognize it. This is done directly
through the Learning Modules web interface and is outside the scope
of this guide.


Licensing
=========
PyLmod is licensed under the BSD license, version January 9, 2008.  See
LICENSE for the full text of the license.


