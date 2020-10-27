# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring, missing-function-docstring

import os
from pathlib import Path


class ProgramNotFound:
    # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "NOT-FOUND:{0}".format(self.name)


class ProgramFinder:
    svn = None      # subversion
    hg = None       # mercurial

    @classmethod
    def can_run(cls, program):
        EXIT_SUCCESS = 0
        result = os.system("{} --version".format(program))
        return result == EXIT_SUCCESS

    @classmethod
    def find_program(cls, name):
        program = getattr(cls, name, None)
        if program is not None:
            return program

        # -- FIRST-CALL: Locate the program.
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            program = Path(directory)/name
            if program.exists() and cls.can_run(program):
                # -- NOTE: Some facade-program installation exist that fail.
                # EXAMPLE on macOS: /usr/bin/svn
                #   svn: error: The subversion ... no longer provided by Xcode.
                setattr(cls, name, program)  # Memoize it.
                return program
        # -- NOT FOUND:
        program = ProgramNotFound(program)
        setattr(cls, name, program)  # Memoize it.
        return program

    @classmethod
    def find_subversion(cls):
        return cls.find_program("svn")

    @classmethod
    def find_mercurial(cls):
        return cls.find_program("hg")

    @classmethod
    def has_subversion(cls):
        return not isinstance(cls.find_program("svn"), ProgramNotFound)

    @classmethod
    def has_mercurial(cls):
        return not isinstance(cls.find_program("hg"), ProgramNotFound)

    # -- ALIASES:
    has_svn = has_subversion
    has_hg = has_mercurial
