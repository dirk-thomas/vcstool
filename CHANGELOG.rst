^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package vcstool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

0.1.34 (2018-03-09)
-------------------
* add explicit dependency on setuptools (`#65 <https://github.com/dirk-thomas/vcstool/issues/65>`_)

0.1.33 (2018-03-01)
-------------------
* add import --recursive option for git submodules (`#63 <https://github.com/dirk-thomas/vcstool/pull/63>`_)

0.1.32 (2017-12-06)
-------------------
* add --nested option to all verb except import (`#58 <https://github.com/dirk-thomas/vcstool/issues/58>`_)

0.1.31 (2017-09-17)
-------------------
* ensure to interpret version as string (`#54 <https://github.com/dirk-thomas/vcstool/issues/54>`_)

0.1.30 (2017-09-13)
-------------------
* add --retry option to import verb (`#52 <https://github.com/dirk-thomas/vcstool/issues/52>`_)

0.1.29 (2017-08-09)
-------------------
* add support for zip for import (`#51 <https://github.com/dirk-thomas/vcstool/pull/51>`_)
* choose default parallel workers based on cpu count (`#50 <https://github.com/dirk-thomas/vcstool/pull/50>`_)

0.1.28 (2017-07-23)
-------------------
* allow log --limit in combination with other --limit-* options (`#47 <https://github.com/dirk-thomas/vcstool/pull/47>`_)
* honor isatty for colorizing output (`#45 <https://github.com/dirk-thomas/vcstool/pull/45>`_)

0.1.27 (2017-05-31)
-------------------
* fix exit condition in loop  (regression introduced in 0.1.25) (`#44 <https://github.com/dirk-thomas/vcstool/pull/44>`_)

0.1.26 (2017-05-29)
-------------------
* fix regression of added dependencies  (regression introduced in 0.1.25) (`#42 <https://github.com/dirk-thomas/vcstool/pull/42>`_)

0.1.25 (2017-05-27)
-------------------
* process subfolders sequentially (`#41 <https://github.com/dirk-thomas/vcstool/pull/41>`_)

0.1.24 (2017-04-27)
-------------------
* add --force option to import verb (`#37 <https://github.com/dirk-thomas/vcstool/pull/37>`_)

0.1.23 (2017-03-20)
-------------------
* do not hide git status when ahead or behind (`#36 <https://github.com/dirk-thomas/vcstool/pull/36>`_)

0.1.22 (2017-03-02)
-------------------
* do not show 'same repo' when using --hide (`#34 <https://github.com/dirk-thomas/vcstool/pull/34>`_)

0.1.21 (2016-09-19)
-------------------
* change git import behavior to handle detached HEADs better (`#31 <https://github.com/dirk-thomas/vcstool/pull/31>`_)
* add messages to debug currently processed jobs when using --debug (`#30 <https://github.com/dirk-thomas/vcstool/issues/30>`_)

0.1.20 (2016-08-22)
-------------------
* fix hg colorization which only worked for some repos due to a race condition

0.1.19 (2016-08-15)
-------------------
* fix export if local branch has same name as ref (`#29 <https://github.com/dirk-thomas/vcstool/pull/29>`_)

0.1.18 (2016-07-21)
-------------------
* do not require explicit color.mode option for hg but consider default value

0.1.17 (2016-06-17)
-------------------
* fix tar extraction on Windows (`#27 <https://github.com/dirk-thomas/vcstool/issues/27>`_)

0.1.16 (2016-06-01)
-------------------
* fix import tar with Python 3 (`#25 <https://github.com/dirk-thomas/vcstool/issues/25>`_)
* add command line option to specify number of worker threads
* do not require explicit color.ui option but consider default value

0.1.15 (2015-09-24)
-------------------
* make version attribute in imported yaml file optional for git repos (`#19 <https://github.com/dirk-thomas/vcstool/issues/19>`_)
* if printing output fails due to encoding problems try again replacing the problematic characters
* add short option for --hide-empty, use -s and --skip-empty as synonyms (`#17 <https://github.com/dirk-thomas/vcstool/pull/17>`_)

0.1.14 (2015-05-19)
-------------------
* improve error message when executable is not available (`#16 <https://github.com/dirk-thomas/vcstool/issues/16>`_)

0.1.13 (2015-04-18)
-------------------
* use --rebase when invoking pull on import
* unify branch command behavior showing the current branch, add option --all to list all branches (`#15 <https://github.com/dirk-thomas/vcstool/issues/15>`_)

0.1.12 (2015-03-22)
-------------------
* improve output of export command in case of errors (`#13 <https://github.com/dirk-thomas/vcstool/pull/13>`_)

0.1.11 (2015-03-13)
-------------------
* fix Python 2 (regression introduced in 0.1.10)

0.1.10 (2015-03-12)
-------------------
* change license from BSD to Apache License, Version 2.0
* return code 1 if the command fails for any repository
* fix colored output to be disabled if not isatty and on Windows without ConEmuANSI

0.1.9 (2015-03-11)
------------------
* fix 'import' command for git (regression introduced in 0.1.8)

0.1.8 (2015-03-03)
------------------
* improve error message if command raises an exception
* fix 'export' command for git repositories with multiple remotes (`#11 <https://github.com/dirk-thomas/vcstool/pull/11>`_)

0.1.7 (2014-10-15)
------------------
* add '--limit-tag TAGNAME' option to 'log' command
* fix '--limit-untagged' option of 'log' command for mercurial

0.1.6 (2014-01-17)
------------------
* Python 3 compatibility
* fix '--exact' option of 'export' command for mercurial (`#6 <https://github.com/dirk-thomas/vcstool/issues/6>`_)

0.1.5 (2013-11-03)
------------------
* fix missing dependencies (`#5 <https://github.com/dirk-thomas/vcstool/issues/5>`_)

0.1.4 (2013-09-16)
------------------
* add '--hide-empty' option (`#3 <https://github.com/dirk-thomas/vcstool/issues/3>`_)
* fix 'import' command cloning to wrong path (`#4 <https://github.com/dirk-thomas/vcstool/issues/4>`_)

0.1.3 (2013-06-23)
------------------
* add 'custom' command to run arbitrary vcs commands with user-specified arguments
* add support to import entries of type 'tar' to handle arbitrary rosinstall files
* add missing completion scripts to PIP package
* update several git and hg commands to stay colorized
* fix pull command for git when repo is in a detached state

0.1.2 (2013-01-18)
------------------
* fix entrypoint of import command
* fix parsing of command output with trailing whitespaces
* fix unneccesary import of mako (`#1 <https://github.com/dirk-thomas/vcstool/issues/1>`_)

0.1.1 (2013-01-14)
------------------
* first public release
