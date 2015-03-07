
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as testcommand

VERSION = __import__('pylmod').VERSION

with open('test_requirements.txt') as test_reqs:
    tests_require = test_reqs.readlines(),


class PyTest(testcommand):
    user_options = testcommand.user_options[:]
    user_options += [
        ('coverage', 'C', 'Produce a coverage report for PyLmod'),
        ('pep8', 'P', 'Produce a pep8 report for PyLmod'),
        ('flakes', 'F', 'Produce a flakes report for PyLmod'),

    ]
    coverage = None
    pep8 = None
    flakes = None
    test_suite = False
    test_args = []

    def initialize_options(self):
        testcommand.initialize_options(self)

    def finalize_options(self):
        testcommand.finalize_options(self)
        self.test_suite = True
        self.test_args = []
        if self.coverage:
            self.test_args.append('--cov')
            self.test_args.append('pylmod')
        if self.pep8:
            self.test_args.append('--pep8')
        if self.flakes:
            self.test_args.append('--flakes')

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        # Needed in order for pytest_cache to load properly
        # Alternate fix: import pytest_cache and pass to pytest.main
        import _pytest.config

        pm = _pytest.config.get_plugin_manager()
        pm.consider_setuptools_entrypoints()
        errno = pytest.main(self.test_args)
        sys.exit(errno)


README = open('README.rst').read()

setup(
    name='pylmod',
    version='0.1.0',
    license='BSD',
    author='MIT ODL Engineering',
    author_email='odl-engineering@mit.edu',
    url="http://github.com/mitodl/pylmod",
    description="PyLmod is a Python Implementation of MIT Learning Modules",
    long_description=README,
    packages=find_packages(),
    install_requires=["requests>=2.5.1", ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Programming Language :: Python',
    ],
    test_suite="pylmod.tests",
    tests_require=tests_require,
    cmdclass={"test": PyTest},
    include_package_data=True,
    zip_safe=True,
)
