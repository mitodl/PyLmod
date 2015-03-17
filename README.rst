PyLmod
======
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
record for classes, students, and grades. Its documentation is available
at these links.

MIT Learning Modules web service documentation:

    `Gradebook module doc
    <https://learning-modules-test.mit.edu/service/gradebook/doc.html>`_

    `Membership module doc
    <https://learning-modules-test.mit.edu/service/membership/doc.html>`_

Getting Started
===============
The Learning Modules web service requires authentication by x.509
certificates. You must create an application certificate and configure
the Learning Modules web service to recognize it. MIT developers can
use this `IS&T guide <http://goo.gl/3YcmRh>`_ to create an application
certificate. The `MITx Knowledge Base <https://odl.zendesk.com/hc/en-us/>`_
also contains an article 'MIT Application Certificates" that explains
the steps in greater detail.

Once you have your application certificate you must get the Learning
Modules service to recognize it. The app certificate needs to have
an account on the service and then the proper role(s) in the proper
group(s). Send your application certificate to learningmod-support@mit.edu
with a request for access. Inform them what your application will do and
they will assist in configuring your certificate.

Licensing
=========
PyLmod is licensed under the BSD license, version January 9, 2008.  See
LICENSE for the full text of the license.


