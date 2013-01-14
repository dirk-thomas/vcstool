#!/usr/bin/env python

from setuptools import setup, find_packages
from vcstool import __version__

setup(
    name='vcstool',
    version=__version__,
    packages=find_packages(),
    author='Dirk Thomas',
    author_email='dthomas@willowgarage.com',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@willowgarage.com',
    url='http://www.ros.org/wiki/vcstool',
    download_url='http://pr.willowgarage.com/downloads/vcstool/',
    classifiers=['Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Version Control',
                 'Topic :: Utilities'],
    description='vcstool provides a command line tool to invoke vcs commands on multiple repositories.',
    long_description='''\
vcstool enables batch commands on multiple different vcs repositories. \
Currently it supports git, hg, svn and bzr.''',
    license='BSD',
    data_files=[
        ('share/vcstool-completion', [
            'vcstool-completion/vcs.bash',
            'vcstool-completion/vcs.tcsh',
            'vcstool-completion/vcs.zsh'
        ])
    ],
    entry_points={
        'console_scripts': [
            'vcs = vcstool.commands.vcs:main',
            'vcs-branch = vcstool.commands.branch:main',
            'vcs-diff = vcstool.commands.diff:main',
            'vcs-export = vcstool.commands.export:main',
            'vcs-help = vcstool.commands.help:main',
            'vcs-import = vcstool.commands.import:main',
            'vcs-log = vcstool.commands.log:main',
            'vcs-pull = vcstool.commands.pull:main',
            'vcs-push = vcstool.commands.push:main',
            'vcs-remotes = vcstool.commands.remotes:main',
            'vcs-status = vcstool.commands.status:main',
        ]
    }
)
