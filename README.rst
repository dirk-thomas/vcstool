What is vcstool?
================

Vcstool is a version control system (VCS) tool, designed to make working with multiple repositories easier.


How does it work?
-----------------

Vcstool operates on any folder from where it recursively searches for supported repositories.
On these repositories vcstool invokes the native VCS client with the requested command (i.e. *diff*).


Which VCS types are supported?
------------------------------

Vcstool supports `Git <http://git-scm.com>`_, `Mercurial <http://git-scm.comhttp://mercurial.selenic.com>`_, `Subversion <http://subversion.apache.org>`_, `Bazaar <http://bazaar.canonical.com/en/>`_.


How to use vcstool?
-------------------

The script ``vcs`` can be used similar to the VCS clients ``git``, ``hg`` etc.
The ``help`` command provides a list of available commands with an additional description::

  vcs help

By default vcstool searches for repositories under the current folder.
Optionally one path (or multiple paths) can be passed to search for repositories at different locations::

  vcs status /path/to/several/repos /path/to/other/repos /path/to/single/repo


Exporting and importing sets of repositories
--------------------------------------------

Vcstool can export and import all the information required to reproduce the versions of a set of repositories.
Vcstool uses a simple `YAML <http://www.yaml.org/>`_ format to encode this information.
This format includes a root key ``repositories`` under which each local repository is described by a dictionary keyed by its relative path.
Each of these dictionaries contains keys ``type``, ``url``, and ``version``.

This results in something similar to the following for a set of two repositories (`vcstool <https://github.com/dirk-thomas/vcstool>`_ cloned via Git and `rosinstall <http://github.com/vcstools/rosinstall>`_ checked out via Subversion):

.. code-block:: yaml

  repositories:
    vcstool:
      type: git
      url: git@github.com:dirk-thomas/vcstool.git
      version: master
    old_tools/rosinstall:
      type: svn
      url: https://github.com/vcstools/rosinstall/trunk
      version: 748


Export set of repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``vcs export`` command outputs the path, vcs type, URL and version information for all repositories in `YAML <http://www.yaml.org/>`_ format.
The output is usually piped to a file::

  vcs export > my.repos

If the repository is currently on the tip of a branch the branch is followed.
This implies that a later import might fetch a newer revision if the branch has evolved in the meantime.
Furthermore if the local branch has evolved from the remote repository an import might not result in the exact same state.

To make sure to store the exact revision in the exported data use the command line argument ``--exact``.
Since a specific revision is not tied to neither a branch nor a remote (for Git and Mercurial) the tool will check if the current hash exists in any of the remotes.
If it exists in multiple the remotes ``origin`` and ``upstream`` are considered before any other in alphabetical order.


Import set of repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``vcs import`` command clones all repositories which are passed in via stdin in YAML format.
Usually the data of a previously exported file is piped in::

  vcs import < my.repos

The ``import`` command also supports input in the `rosinstall file format <http://www.ros.org/doc/independent/api/rosinstall/html/rosinstall_file_format.html>`_.
Only for this command vcstool supports a pseudo client ``tar`` which fetches a tarball from an URL and unpacks its content.


Advanced features
-----------------

Show log since last tag
~~~~~~~~~~~~~~~~~~~~~~~

The ``vcs log`` command supports the argument ``--limit-untagged`` which will output the log for all commits since the last tag.


Run arbitrary comands
~~~~~~~~~~~~~~~~~~~~~

The ``vcs custom`` command enables to pass arbitrary user-specified arguments to the vcs invocation.
The set of repositories to operate on can optionally be restricted by the type:

  vcs custom --git --args log --oneline -n 10

If the command should work on multiple repositories make sure to pass only generic arguments which work for all of these repository types.


How to install vcstool?
=======================

On Debian-based platforms the recommended method is to install the package *python-vcstool*.
On Ubuntu this is done using *apt-get*::

  sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
  sudo apt-key adv --keyserver hkp://pool.sks-keyservers.net --recv-key 0xB01FA116
  sudo apt-get update
  sudo apt-get install python-vcstool

On other Systems, use the `PyPI <http://pypi.python.org>`_ package::

  sudo pip install vcstool


Setup auto-completion
---------------------

For the shells *bash*, *tcsh* and *zsh* vcstool can provide auto-completion of the various VCS commands.
In order to enable that feature the shell specific completion file must be sourced.

For *bash* append the following line to the ``~/.bashrc`` file::

  source /usr/share/vcstool-completion/vcs.bash

For *tcsh* append the following line to the ``~/.cshrc`` file::

  source /usr/share/vcstool-completion/vcs.tcsh

For *zsh* append the following line to the ``~/.zshrc`` file::

  source /usr/share/vcstool-completion/vcs.zsh


How to contribute?
==================

How to report problems?
-----------------------

Before reporting a problem please make sure to use the latest version.
Issues can be filled on `GitHub <https://github.com/dirk-thomas/vcstool/issues>`_ after making sure that this problem has not yet been reported.

Please make sure to include as much information, i.e. version numbers from vcstool, operating system, Python and a reproducible example of the commands which expose the problem.


How to try the latest changes?
------------------------------

Sourcing the ``setup.sh`` file prepends the ``src`` folder to the ``PYTHONPATH`` and the ``scripts`` folder to the ``PATH``.
Then vcstool can be used with the commands ``vcs-COMMAND`` (note the hyphen between ``vcs`` and ``command`` instead of a space).

Alternatively the *develop* command from Python setuptools can be used:
  sudo python setup.py develop
