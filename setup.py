import sys
from setuptools import setup


__version__ = (0, 1)

setup(
    name="ga-wsgi-client",
    description="A WSGI middleware package for tracking web usage with Google Analytics",
    keywords="web wsgi google",
    packages=['ga_wsgi_client'],
    version='.'.join(str(d) for d in __version__),
    url="http://www.pacificclimate.org/",
    author="James Hiebert",
    author_email="hiebert@uvic.ca",
    install_requires=['webob'],
    tests_require=[],
    zip_safe=True,
    classifiers='''Development Status :: 2 - Pre-Alpha
Environment :: Console
Environment :: Web Environment
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License (GPL)
Operating System :: OS Independent
Programming Language :: Python
Topic :: Internet
Topic :: Internet :: WWW/HTTP :: WSGI
Topic :: Software Development :: Libraries :: Python Modules'''.split('\n')
)
