import argparse
import os
from pathlib import Path
import sys

from vcstool.crawler import find_repositories
from vcstool.executor import ansi
from vcstool.executor import execute_jobs
from vcstool.executor import generate_jobs
from vcstool.executor import output_repositories
from vcstool.executor import output_results
from vcstool.streams import set_streams

from .command import add_common_arguments
from .command import Command


class ExportCommand(Command):

    command = 'export'
    help = 'Export the list of repositories'

    def __init__(self, args):
        super(ExportCommand, self).__init__(args)
        self.exact = args.exact or args.exact_with_tags
        self.with_tags = args.exact_with_tags
        self.viewpoint = Path(args.viewpoint).absolute()


def get_parser():
    parser = argparse.ArgumentParser(
        description='Export the list of repositories', prog='vcs export')
    group = parser.add_argument_group('"export" command parameters')
    group.add_argument(
        '--view-point', '--view', dest='viewpoint', default='.',
        type=Path, metavar="DIRECTORY",
        help='View point to compute repository names')
    group_exact = group.add_mutually_exclusive_group()
    group_exact.add_argument(
        '--exact', action='store_true', default=False,
        help='Export commit hashes instead of branch names')
    group_exact.add_argument(
        '--exact-with-tags', action='store_true', default=False,
        help='Export unique tag names or commit hashes instead of branch '
             'names')
    return parser


def output_export_data(result, hide_empty=False):
    # errors are handled by a separate function
    if result['returncode']:
        return

    try:
        lines = []
        lines.append('  %s:' % result['path'])
        lines.append('    type: ' + result['client'].__class__.type)
        export_data = result['export_data']
        lines.append('    url: ' + export_data['url'])
        if 'version' in export_data and export_data['version']:
            lines.append('    version: ' + export_data['version'])
        print('\n'.join(lines))
    except KeyError as e:
        print(
            ansi('redf') + (
                "Command '%s' failed for path '%s': %s: %s" % (
                    result['command'].__class__.command,
                    result['client'].path, e.__class__.__name__, e)) +
            ansi('reset'),
            file=sys.stderr)


def output_error_information(result, hide_empty=False):
    # successful results are handled by a separate function
    if not result['returncode']:
        return

    if result['returncode'] == NotImplemented:
        color = 'yellow'
    else:
        color = 'red'

    line = '%s: %s' % (result['path'], result['output'])
    print(ansi('%sf' % color) + line + ansi('reset'), file=sys.stderr)


def get_relative_path_of_result(result):
    client = result['client']
    return os.path.relpath(client.path, result['command'].paths[0])


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)

    parser = get_parser()
    add_common_arguments(parser, skip_hide_empty=True, path_nargs='*')
    args = parser.parse_args(args)
    if not args.viewpoint or not args.viewpoint.is_dir():
        parser.error("viewpoint={}: directory does not exist".format(
                     args.viewpoint))
    command = ExportCommand(args)
    clients = find_repositories(command.paths, nested=command.nested)
    if command.output_repos:
        output_repositories(clients)
    jobs = generate_jobs(clients, command)
    results = execute_jobs(jobs, number_of_workers=args.workers)

    # -- STEP: Compute repository.path relative to viewpoint.
    viewpoint = str(command.viewpoint)
    uses_other_viewpoint = (command.viewpoint != Path.cwd() or
                            command.paths != [os.curdir])
    for result in results:
        if uses_other_viewpoint:
            # -- USE VIEW-POINT: repository.path relative from viewpoint.
            repository_path = os.path.abspath(result['client'].path)
            repository_path = os.path.relpath(repository_path, viewpoint)
        else:
            # -- DEFAULT CASE: viewpoint='.' (CWD)
            repository_path = get_relative_path_of_result(result)
        result['path'] = repository_path

    print('repositories:')
    output_results(results, output_handler=output_export_data)
    output_results(results, output_handler=output_error_information)

    any_error = any(r['returncode'] for r in results)
    return 1 if any_error else 0


if __name__ == '__main__':
    sys.exit(main())
