#!/usr/bin/env python

import sys

from setuptools import find_packages
from setuptools import setup
from vcstool import __version__

install_requires = ['PyYAML', 'setuptools']
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    install_requires.append('argparse')

setup(
    name='vcstool',
    version=__version__,
    install_requires=install_requires,
    packages=find_packages(),
    author='Dirk Thomas',
    author_email='dthomas@osrfoundation.org',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@osrfoundation.org',
    url='https://github.com/dirk-thomas/vcstool',
    download_url='http://download.ros.org/downloads/vcstool/',
    classifiers=['Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Version Control',
                 'Topic :: Utilities'],
    description='vcstool provides a command line tool to invoke vcs commands '
        'on multiple repositories.',
    long_description='\
vcstool enables batch commands on multiple different vcs repositories. \
Currently it supports git, hg, svn and bzr.',
    license='Apache License, Version 2.0',
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
            'vcs-bzr = vcstool.commands.custom:bzr_main',
            'vcs-custom = vcstool.commands.custom:main',
            'vcs-diff = vcstool.commands.diff:main',
            'vcs-export = vcstool.commands.export:main',
            'vcs-git = vcstool.commands.custom:git_main',
            'vcs-help = vcstool.commands.help:main',
            'vcs-hg = vcstool.commands.custom:hg_main',
            'vcs-import = vcstool.commands.import_:main',
            'vcs-log = vcstool.commands.log:main',
            'vcs-pull = vcstool.commands.pull:main',
            'vcs-push = vcstool.commands.push:main',
            'vcs-remotes = vcstool.commands.remotes:main',
            'vcs-status = vcstool.commands.status:main',
            'vcs-svn = vcstool.commands.custom:svn_main',
            'vcs-validate = vcstool.commands.validate:main',
        ]
    }
)
