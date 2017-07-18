# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages

with open('README.md') as file:
    long_description = file.read()

setup(
  name='django-nagios-cache',
  packages=find_packages(exclude=['build', 'demo']),
  version='0.1.6',
  description='A Django library that sync data from a Nagios/Icinga server.',
  long_description=long_description,
  author='Sören Berger',
  author_email='soeren.berger@u1337.de',
  url='https://github.com/soerenbe/django-nagios-cache',
  download_url='https://github.com/soerenbe/django-nagios-cache/tarball/0.2.0',
  keywords=['django', 'nagios', 'icinga'],
  install_requires=['django', 'requests', 'parsedatetime', 'pytz'],
  license='GPL-3',
  classifiers=[
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
  ],
)
