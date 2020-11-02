# -*- coding_ UTF-8 -*-
"""Test support for pytest test functionality related to :mod:`vcstool` module."""  # noqa: E501

# -- HINT: Test support functionality should be refactored out into own module
import os
from pathlib import Path
from test.test_commands import get_expected_output, run_command


# -- SETUP PYTHON SEARCH PATH:
HERE = Path(__file__).parent.resolve()
VERBOSE = os.environ.get("VERBOSE", "no") == "yes"


# -----------------------------------------------------------------------------
# TEST SUPPORT
# -----------------------------------------------------------------------------
def make_imported_workspace(directory, repos_filename, expected_output_name):
    repos_filename = Path(repos_filename)
    if not repos_filename.is_absolute():
        repos_filename = Path(HERE/repos_filename).resolve()

    output = run_command('import', ['--input=%s' % repos_filename],
                         cwd=str(directory))
    if VERBOSE:
        print(output.decode(encoding="UTF-8"))

    # -- HINT: newer git versions don't append three dots after the commit hash
    expected = get_expected_output(expected_output_name)
    assert output == expected or output == expected.replace(b'... ', b' ')
    return directory


def make_imported_workspace_by_name(directory, name):
    repos_filename = '{0}.repos'.format(name)
    expected_output_name = '{0}.imported'.format(name)
    return make_imported_workspace(directory, repos_filename,
                                   expected_output_name)
