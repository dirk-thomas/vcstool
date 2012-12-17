#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='vcstool',
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    author='Dirk Thomas',
    author_email='dthomas@willowgarage.com',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@willowgarage.com',
    url='http://www.ros.org/wiki/vcstool',
    download_url='http://pr.willowgarage.com/downloads/vcstool/',
    keywords=['VCS'],
    classifiers=['Programming Language :: Python',
                 'License :: OSI Approved :: BSD License'],
    description='vcstool provides a command line tool to invoke vcs commands on multiple repositories.',
    long_description='''\
vcstool enables batch commands on multiple different vcs repositories. \
Currently it supports git, hg, svn and bzr.''',
    license='BSD',
    test_suite='test',
    entry_points={
        'console_scripts': [
            'vcstool-diff = vcstool.command.diff:main',
            'vcstool-pull = vcstool.command.pull:main',
            'vcstool-push = vcstool.command.push:main',
            'vcstool-remotes = vcstool.command.remotes:main',
            'vcstool-status = vcstool.command.status:main',
        ]
    }
)
