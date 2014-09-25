#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    print '(WARNING: importing distutils, not setuptools!)'
    from distutils.core import setup

# setup information

setup(name = 'twine',
      
      version = '1.8.0',

      description = 'twine Web browsing language',
      author = 'C. Titus Brown and Ben R. Taylor',
      author_email = 'titus@idyll.org',
      license='MIT',

      packages = ['twine', 'twine.extensions',
                  'twine.extensions.match_parse'],

      # allow both 
      entry_points = dict(console_scripts=['twine = twine.shell:main'],),
      scripts = ['twill-fork'],
      
      maintainer = 'C. Titus Brown',
      maintainer_email = 'titus@idyll.org',

      url = 'http://twill.idyll.org/',
      long_description = """\
A scripting system for automating Web browsing.  Useful for testing
Web pages or grabbing data from password-protected sites automatically.
""",
      classifiers = ['Development Status :: 4 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'Intended Audience :: System Administrators',
                     'License :: OSI Approved :: MIT License',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Programming Language :: Other Scripting Engines',
                     'Topic :: Internet :: WWW/HTTP',
                     'Topic :: Software Development :: Testing',
                     ],

      test_suite = 'nose.collector'
      )
