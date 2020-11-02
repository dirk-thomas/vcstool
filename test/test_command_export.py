# -*- coding_ UTF-8 -*-
# noqa: E501
"""
Unit tests for the `issue #177`_ related to import/export idempotency.

Import/export idempotency means:

* if I use "vcs import --input=my.repos" or
  ("vcs import some/directory --input=my.repos")
  when I use "vcs export > my.repos2"
  then the files "my.repos" and "my.repos2" should be the same
  (if the vcs-repos-data-format were used for the "my.repos" file).

* Therefore, you can use "vcs import ..." / "vcs export ..." cycles
  as often as you want, the generated repos-file stay the same
  (can be created in a reproducible way)
  and no additional directory-tree(s) are created during additional runs.

PROBLEMS WITH CURRENT EXPORTED DATA:

* CASE 1: Without git-anchor-repository as current-working-directory

  Normal export works (from import-directory location), but:

  - "vcs export" from within a repo-directory has basename instead of ".".
  - "vcs export --nested some/subdir" cuts prefix "some/subdir/" from repo-name

  REASON: "vcs export" does not distinguish between the two concepts:

  * filter (which directory-subtree is of interest) and
  * view-point (from which directory the repository-directory names are seen)

* CASE 2A: With anchor-repository as current-working-directory

  DEFINITION: anchor-directory := current-working-directory (as absolute path)
  anchor-directory is root-directory of the anchor-repository
  (that contains ".git/")

  Repo locations are prefixed w/ basename of git-anchor-repository directory.
  Therefore, the exported repo data looks like it was exported
  from the parent-directory of the current-working-directory

  VIEW POINT: .. (parent-directory)
  => vcs export --nested $(basename anchor-directory)
  => vcs export --nested $(relpath_to anchor-directory)  # SAME-AS-ABOVE
  => repos-file-data contains: "$(basename anchor-directory)/" prefix in name

* CASE 2B: Some parent of anchor-repository as current-working-directory

  EXAMPLE view point: anchor-directory/../ == current-working-directory
  => vcs export --nested $(relpath_to anchor-directory)
  => repos-file-data contains: "$(relpath_to anchor-directory)"
     prefixes in name(s)

DESIRED CHANGES:

* BACKWARD COMPATIBLE (if this is desired; see impact below):
  Current implementation state should be reproducible,
  but by using other means, like additional CLI options.

* CASE 2A: Should use relpath_to:current-working-directory instead of
  relpath_from:parent-directory:to:current-working-directory

* CASE 2B: Same as CASE 2A (with relpath_to:... instead of basename),
  provides location(s) to repos as name(s).

* CASE 1: Provides locations in exported repo-names
  (same behaviour as in CASE 2A and CASE 2B)

BACKWARD COMPATIBILITY (with additional options; reproduces current state):

* CASE 1  with "vcs export --nested --view-point=subdir subdir"
  (SAME AS: "cd subdir; vcs export --nested")

* CASE 2A with "vcs export --nested --view-point=.."

CLI CHANGES:

* paths args: Used to filter/select which directory-subtrees are exported.
  Cardinality: 0..N = many (was: 0..1 = optional).
  FORMERLY: paths are used as filter and define the viewpoint.

* ADDED: --view-point option, used to define the viewpoint.

NEW OPTIONS (optional):

* --view-point : path = "."; cardinality: 0..1 (optional)

    Provides the view from which the repo-location(s) should be computed
    with view_point_directory.relpath_to(discovered_repo_dir).

    ALTERNATIVE OPTION NAME CANDIDATE: --view=..., --viewed-from=...

ADDITIONAL MORE USEFUL OPTIONS (not implemented / covered here):

* --exclude : path; cardinality: 0..N (optional-many)

    Provides path or relpath from current-working-directory
    that should be excluded in the exported repos-data.
    The excluded path filters out any repository(s)
    that is/are located in this directory or below it.

.. seealso:: `issue #177`_

    RELATED:

    * https://github.com/dirk-thomas/vcstool/pull/102
    * https://github.com/dirk-thomas/vcstool/issues/101

.. _`issue #177`: https://github.com/dirk-thomas/vcstool/issues/177
"""

# -- HINT: Test support functionality should be refactored out into own module
from pathlib import Path
import shutil
import subprocess
import sys
from test.test_commands import get_expected_output, run_command
from test.workspace_util import make_imported_workspace_by_name

import pytest

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
TOPDIR = Path(__file__).parent.parent.resolve()
PYTHON_VERSION = sys.version_info[:2]
PY37_OR_GREATER = (PYTHON_VERSION >= (3, 7))


# -----------------------------------------------------------------------------
# TEST SUPPORT
# -----------------------------------------------------------------------------
def print_output(output):
    if not isinstance(output, str):
        output = output.decode(encoding='UTF-8')
    print(output)


def run_vcs(command, *args, cwd=".", capture_output=True, check=False,
            verbose=False, **run_kwargs):
    """Run a vcs command as subprocess by using subprocess.run()."""
    cwd = str(cwd)
    command2 = "{prefix}/scripts/vcs-{command}".format(command=command,
                                                       prefix=str(TOPDIR))
    python = sys.executable
    args2 = [python, command2] + list(args)
    if verbose:
        print("run: %s (cwd=%s)" % (args2, cwd))
    if PY37_OR_GREATER:
        # -- SINCE py37: capture_output : bool = False
        result = subprocess.run(args2, capture_output=capture_output,
                                cwd=cwd, check=check, **run_kwargs)
    else:
        # -- CASE py35, py36:
        result = subprocess.run(args2, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=cwd, check=check, **run_kwargs)
    return result


def assert_repositories_output_matches(output, expected, encoding='UTF-8'):
    """Assert that vcs-export output matches the expected output.

    * Ignores any diagnostic output that occurs before repositories dump
    * Ignores any trailing whitespace-line diffs
    * Converts output, expected-output from bytes into string
      for better diffs in pytest (if assertion fails)
    """
    # -- CONVERT BYTES-TO-STRING
    # REASON: Better diffs in assert-statements
    output2 = output
    expected2 = expected
    if not isinstance(output, str):
        output2 = output.decode(encoding=encoding).rstrip()
    if not isinstance(expected, str):
        expected2 = expected.decode(encoding=encoding).rstrip()

    # -- STEP: Discover begin of repository-dump
    pos = output2.index("repositories:")
    assert pos >= 0, "REQUIRE: repositories in output:\n%s" % output2
    output2 = output2[pos:]

    # -- VERIFY:
    assert output2 == expected2


# -----------------------------------------------------------------------------
# TEST FIXTURES
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def workspace_without_anchor(tmp_path_factory):  # noqa: E501
    """Create workspace with imported repos (export: CASE 1).

    * Without anchor-directory / anchor-repository
    * Multiple repositories

    .. notes::

        * FIXTURE LIFECYCLE: Only setup/teardown once per test-session.
        * WORKSPACE LIFECYCLE:
          workspace directory (tmp_path) is automatically cleaned up
        * workspace directory resides in a tmp-directory

    .. seealso:: `tmp_path <https://docs.pytest.org/en/stable/tmpdir.html>`_

    :return: Workspace directory (as pathlib.Path) as temporary directory.
    """
    workspace_directory = tmp_path_factory.mktemp("workspace_without_anchor")
    print("workspace_without_anchor: directory={0}".format(workspace_directory))  # noqa: E501
    yield make_imported_workspace_by_name(workspace_directory,
                                          name="export_case1")
    # -- CLEANUP:
    shutil.rmtree(workspace_directory, ignore_errors=True)


@pytest.fixture(scope="session")
def workspace_with_anchor(tmp_path_factory):
    """Create workspace with imported repos (export: CASE 2A, 2B).

    * With anchor-directory / anchor-repository
    * With sub-repository(s) below anchor-directory

    :return: Workspace (temporary) directory (as pathlib.Path)
    """
    workspace_directory = tmp_path_factory.mktemp("workspace_with_anchor")
    print("workspace_with_anchor: directory={0}".format(workspace_directory))  # noqa: E501
    yield make_imported_workspace_by_name(workspace_directory,
                                          name="export_case2")
    # -- CLEANUP:
    shutil.rmtree(workspace_directory, ignore_errors=True)


# -----------------------------------------------------------------------------
# TEST SUITE
# -----------------------------------------------------------------------------
class TestExportCommand:
    NESTED_ARGS = ['--nested', '--exact-with-tags']

    def test_export_case1(self, workspace_without_anchor):
        # -- USECASE: vcs export --nested
        # with: CWD=.
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export', args=self.NESTED_ARGS,
                             cwd=workspace_directory)
        print_output(output)
        expected = get_expected_output('export_case1.exported')
        assert_repositories_output_matches(output, expected)

    def test_export_case1_with_cwd_subdir(self, workspace_without_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested
        # with: CWD=immutable
        workspace_directory = workspace_without_anchor
        output = run_command('export', args=self.NESTED_ARGS,
                             cwd=str(workspace_directory/"immutable"))
        print_output(output)
        expected_name = 'export_case1.cwd_subdir.exported'
        expected = get_expected_output(expected_name)
        assert_repositories_output_matches(output, expected)

    def test_export_case1_with_subdir_arg(self, workspace_without_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested immutable
        # with: CWD=.
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export', args=self.NESTED_ARGS + ['immutable'],
                             cwd=workspace_directory)
        print_output(output)
        # -- SAME AS: export_case1.exported
        # REASON: paths select only directory-subtree to include in export
        expected = get_expected_output('export_case1.exported')  # noqa: E501
        assert_repositories_output_matches(output, expected)

    def test_export_case1_with_subdir2_arg(self, workspace_without_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested immutable/vcstool_tag
        # with: CWD=.
        # NOTE: Selects only immutable/vcstool_tag repository to be included.
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export', args=self.NESTED_ARGS + [
                             'immutable/vcstool_tag'],
                             cwd=workspace_directory)
        print_output(output)
        expected = get_expected_output('export_case1.with_subdir2.exported')  # noqa: E501
        assert_repositories_output_matches(output, expected)

    def test_export_case1_with_many_paths_args(self, workspace_without_anchor):    # noqa: E501
        # -- USECASE: vcs export --nested immutable/vcstool_tag immutable/vcstool_master  # noqa: E501
        # with: CWD=.
        # NOTE: Manually selects both repositories (ALL-REPOS) to be included.
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export', args=self.NESTED_ARGS + [
                             'immutable/vcstool_tag',
                             'immutable/vcstool_master'],
                             cwd=workspace_directory)
        print_output(output)
        # -- SAME AS: export_case1.exported => Includes ALL-REPOS.
        expected = get_expected_output('export_case1.exported')  # noqa: E501
        assert_repositories_output_matches(output, expected)

    def test_export_case1_with_viewpoint_subdir(self, workspace_without_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested --view-point=immutable
        # with: CWD=.
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export', args=self.NESTED_ARGS + [
                             '--view-point=immutable'],
                             cwd=workspace_directory)
        print_output(output)
        expected = get_expected_output('export_case1.viewpoint_subdir.exported')  # noqa: E501
        assert_repositories_output_matches(output, expected)

    def test_export_case1_with_viewpoint_subdir_and_subdir_arg(self, workspace_without_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested --view-point=immutable immutable
        # with: CWD=.
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export', args=self.NESTED_ARGS + [
                             '--view-point=immutable', 'immutable'],
                             cwd=workspace_directory)
        print_output(output)
        # -- SAME AS: export_case1.cwd_subdir.exported
        expected = get_expected_output('export_case1.cwd_subdir.exported')  # noqa: E501
        assert_repositories_output_matches(output, expected)

    def test_export_case2a(self, workspace_with_anchor):
        # -- USECASE: vcs export --nested
        # with: CWD=anchor
        workspace_directory = workspace_with_anchor
        output = run_command('export', args=self.NESTED_ARGS,
                             cwd=str(workspace_directory/"anchor"))
        print_output(output)
        expected = get_expected_output('export_case2a.exported')
        assert_repositories_output_matches(output, expected)

    def test_export_case2a_with_viewpoint_parentdir(self, workspace_with_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested --view-point=..
        # with: CWD=anchor
        workspace_directory = workspace_with_anchor
        output = run_command('export',
                             args=self.NESTED_ARGS + ['--view-point=..'],
                             cwd=str(workspace_directory/"anchor"))
        print_output(output)

        # -- SAME AS: export_case2b.exported
        expected = get_expected_output('export_case2b.exported')
        assert_repositories_output_matches(output, expected)

    def test_export_case2a_with_subdir1_arg(self, workspace_with_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested immutable
        # with: CWD=anchor
        # NOTE: Select only subdir repository(s) to be included in vcs-export
        workspace_directory = workspace_with_anchor
        output = run_command('export', args=self.NESTED_ARGS + ['immutable'],
                             cwd=str(workspace_directory/"anchor"))
        print_output(output)
        expected_name = 'export_case2a.with_subdir.exported'
        expected = get_expected_output(expected_name)
        assert_repositories_output_matches(output, expected)

    def test_export_case2a_with_viewpoint_and_subdir1_arg(self, workspace_with_anchor):  # noqa: E501
        # -- USECASE: vcs export --nested --viewpoint=immutable immutable
        # with: CWD=anchor
        # NOTE: Select only subdir repository(s) to be included in vcs-export
        workspace_directory = workspace_with_anchor
        output = run_command('export', args=self.NESTED_ARGS + [
                             '--view-point=immutable', 'immutable'],
                             cwd=str(workspace_directory/"anchor"))
        print_output(output)
        expected_name = 'export_case2a.with_viewpoint_and_subdir.exported'  # noqa: E501
        expected = get_expected_output(expected_name)
        assert_repositories_output_matches(output, expected)

    def test_export_case2b(self, workspace_with_anchor):
        # -- USECASE: vcs export --nested
        # with: CWD=.
        workspace_directory = str(workspace_with_anchor)
        output = run_command('export', args=self.NESTED_ARGS,
                             cwd=workspace_directory)
        print_output(output)
        expected = get_expected_output('export_case2b.exported')
        assert_repositories_output_matches(output, expected)

    def test_export_case2b_with_viewpoint_anchor(self, workspace_with_anchor):
        # -- USECASE: vcs export --nested --view-point=anchor
        # with: CWD=.
        workspace_directory = str(workspace_with_anchor)
        output = run_command('export',
                             args=self.NESTED_ARGS + ['--view-point=anchor'],
                             cwd=workspace_directory)
        print_output(output)
        # -- SAME AS: export_case2a.exported
        expected = get_expected_output('export_case2a.exported')
        assert_repositories_output_matches(output, expected)


class TestExportImportIdempotency:
    """Ensures that the export/import/export cycle is idempotent.

    * CASE 1
    * CASE 2A
    * CASE 2B
    """

    NESTED_ARGS = ['--nested', '--exact-with-tags']

    @classmethod
    def run_export_import_export(cls, directory, export_cwd=None,
                                 import_cwd=None, import_dir=None,
                                 export_expected=None, **run_kwargs):
        export_cwd = str(export_cwd or directory)
        import_cwd = str(import_cwd or directory)

        # -- ENSURE: Current vcstool implementation is used.
        # Setup PYTHONPATH to ensure subprocess.run() use it.
        env = run_kwargs.pop('env', {})
        env['PYTHONPATH'] = str(TOPDIR)
        run_kwargs['env'] = env

        # -- STEP 1: export-1
        result = run_vcs('export', *cls.NESTED_ARGS,
                         cwd=export_cwd, **run_kwargs)
        output1 = b'%s\n%s' % (result.stdout, result.stderr or b'')
        print_output(output1)
        print('----')
        assert result.returncode == 0
        if export_expected:
            assert_repositories_output_matches(output1, export_expected)

        print("directory:  {}".format(directory))
        print("import_cwd: {}".format(import_cwd))
        print("export_cwd: {}".format(export_cwd))
        output1 = result.stdout
        repos_file = directory/"my.repos"
        repos_file.write_bytes(output1)

        # -- STEP 2: import
        result = run_vcs('import', '--input={}'.format(repos_file),
                         str(import_dir or '.'),
                         cwd=import_cwd, **run_kwargs)
        output = b'%s\n%s' % (result.stdout, result.stderr or b'')
        print_output(output)
        print('----')
        assert result.returncode == 0

        # -- STEP 3: export-2
        result = run_vcs('export', *cls.NESTED_ARGS, cwd=export_cwd,
                         **run_kwargs)
        output2 = b'%s\n%s' % (result.stdout, result.stderr or b'')
        print_output(output2)
        repos_file.unlink()
        return output1, output2

    def test_export_case1(self, workspace_without_anchor):
        # -- USECASE: vcs export --nested
        # with: CWD=.
        workspace_directory = workspace_without_anchor
        output1, output2 = self.run_export_import_export(workspace_directory)

        expected = get_expected_output('export_case1.exported')
        assert_repositories_output_matches(output1, output2)
        assert_repositories_output_matches(output1, expected)

    def test_export_case2b(self, workspace_with_anchor):
        # -- USECASE: vcs export --nested
        # with: CWD=.
        workspace_directory = workspace_with_anchor
        output1, output2 = self.run_export_import_export(workspace_directory)

        expected = get_expected_output('export_case2b.exported')
        assert_repositories_output_matches(output1, output2)
        assert_repositories_output_matches(output1, expected)

    def test_export_case2a(self, workspace_with_anchor):
        # -- USECASE: vcs export --nested
        # with: CWD=anchor
        workspace_directory = workspace_with_anchor
        expected = get_expected_output('export_case2a.exported')
        output1, output2 = self.run_export_import_export(
            workspace_directory,
            export_cwd=workspace_directory/"anchor",
            import_dir="anchor",
            export_expected=expected
        )

        assert_repositories_output_matches(output1, output2)
        assert_repositories_output_matches(output1, expected)


class TestVcsExportProgramOptions:
    """Ensure that the some command-line options have the desired behavior.

    TESTED COMMAND LINE OPTIONS:

    * ``--view-point=<DIRECTORY>``
    """

    @pytest.mark.parametrize("viewpoint", [
        ".", "..", "immutable", "immutable/.."
    ])
    def test_viewpoint_with_existing_directory_succeeds(
            self, workspace_without_anchor, viewpoint):    # noqa: E501
        workspace_directory = str(workspace_without_anchor)
        output = run_command('export',
                             args=['--view-point={0}'.format(viewpoint)],
                             cwd=workspace_directory)
        print_output(output)

    @pytest.mark.parametrize("viewpoint", [
        "__UNKNOWN_DIR__", "immutable/__UNKNOWN_DIR__", "../__UNKNOWN_DIR__"
    ])
    def test_viewpoint_with_non_existing_directory_fails(
            self, viewpoint, workspace_without_anchor):  # noqa: E501
        workspace_directory = workspace_without_anchor
        result = run_vcs('export', '--view-point={0}'.format(viewpoint),
                         cwd=workspace_directory)

        # -- DIAGNOSTICS:
        print("result.returncode={}".format(result.returncode))
        print(result.stdout.decode(encoding="UTF-8"))
        print("----")
        print(result.stderr.decode(encoding="UTF-8"))

        command_success = (result.returncode == 0)
        expected = b"viewpoint=%s: directory does not exist" % \
                   viewpoint.encode(encoding="UTF-8")
        assert expected in result.stderr
        assert not command_success
