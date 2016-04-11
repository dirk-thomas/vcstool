from __future__ import print_function

import argparse
import os
import sys

from vcstool.crawler import find_repositories
from vcstool.executor import ansi, execute_jobs, generate_jobs, output_repositories, output_results

from .command import add_common_arguments, Command


class ExportCommand(Command):

    command = 'export'
    help = 'Export the list of repositories'

    def __init__(self, args):
        super(ExportCommand, self).__init__(args)
        self.exact = args.exact


def get_parser():
    parser = argparse.ArgumentParser(description='Export the list of repositories', prog='vcs export')
    group = parser.add_argument_group('"export" command parameters')
    group.add_argument('--exact', action='store_true', default=False, help='Export exact commit hash instead of branch names')
    return parser


def output_export_data(result, hide_empty=False):
    # errors are handled by a separate function
    if result['returncode']:
        return

    path = get_path_of_result(result)

    try:
        lines = []
        lines.append('  %s:' % path)
        lines.append('    type: %s' % result['client'].__class__.type)
        export_data = result['export_data']
        lines.append('    url: %s' % export_data['url'])
        if 'version' in export_data and export_data['version']:
            lines.append('    version: %s' % export_data['version'])
        print('\n'.join(lines))
    except KeyError as e:
        print(ansi('redf') + ("Command '%s' failed for path '%s': %s: %s" % (result['command'].__class__.command, result['client'].path, e.__class__.__name__, e)) + ansi('reset'), file=sys.stderr)


def output_error_information(result, hide_empty=False):
    # successful results are handled by a separate function
    if not result['returncode']:
        return

    if result['returncode'] == NotImplemented:
        color = 'yellow'
    else:
        color = 'red'

    path = get_path_of_result(result)
    line = '%s: %s' % (path, result['output'])
    print(ansi('%sf' % color) + line + ansi('reset'), file=sys.stderr)


def get_path_of_result(result):
    client = result['client']
    path = os.path.relpath(client.path, result['command'].paths[0])
    if path == '.':
        path = os.path.basename(os.path.abspath(client.path))
    return path


def main(args=None):
    parser = get_parser()
    add_common_arguments(parser, skip_hide_empty=True, single_path=True)
    args = parser.parse_args(args)

    command = ExportCommand(args)
    clients = find_repositories(command.paths)
    if command.output_repos:
        output_repositories(clients)
    jobs = generate_jobs(clients, command)
    results = execute_jobs(jobs, number_of_workers=args.workers)

    print('repositories:')
    output_results(results, output_handler=output_export_data)
    output_results(results, output_handler=output_error_information)

    any_error = any([r['returncode'] != 0 for r in results])
    return 1 if any_error else 0


if __name__ == '__main__':
    sys.exit(main())
