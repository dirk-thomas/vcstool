import sys

stdout = sys.stdout
stderr = sys.stderr


def set_streams(stdout=None, stderr=None):
    _set_streams(stdout_=stdout, stderr_=stderr)


def _set_streams(stdout_=None, stderr_=None):
    global stdout
    global stderr
    if stdout_ is not None:
        stdout = stdout_
    if stderr_ is not None:
        stderr = stderr_
