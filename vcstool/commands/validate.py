from __future__ import print_function

import argparse
import os
import sys

from vcstool.clients import vcstool_clients
from vcstool.commands.import_ import get_repositories
from vcstool.executor import ansi
from vcstool.executor import execute_jobs
from vcstool.streams import set_streams

from .command import add_common_arguments
from .command import Command


class ValidateCommand(Command):

    command = 'validate'
    help = 'Validate the repository list file'

    def __init__(self, args, url, version=None):
        super(ValidateCommand, self).__init__(args)
        self.url = url
        self.version = version
        self.retry = args.retry
        self.real_path = args.real_path

def get_parser():
    parser = argparse.ArgumentParser(
        description='Validate a repositories file', prog='vcs validate')
    group = parser.add_argument_group('"validate" command parameters')
    group.add_argument(
        '--input', type=argparse.FileType('r'), default=sys.stdin)
    group.add_argument(
        '--retry', type=int, metavar='N', default=2,
        help='Retry commands requiring network access N times on failure')
    return parser


def generate_jobs(repos, args):
    jobs = []
    for path, repo in repos.items():
        clients = [c for c in vcstool_clients if c.type == repo['type']]
        if not clients:
            from vcstool.clients.none import NoneClient
            job = {
                'client': NoneClient(path),
                'command': None,
                'cwd': path,
                'output':
                    "Repository type '%s' is not supported" % repo['type'],
                'returncode': NotImplemented
            }
            jobs.append(job)
            continue

        client = clients[0](args.path)
        args.real_path = path
        command = ValidateCommand(
            args, repo['url'],
            str(repo['version']) if 'version' in repo else None)
        job = {'client': client, 'command': command}
        jobs.append(job)
    return jobs


def output_result(result, hide_empty=False):
    from vcstool.streams import stdout
    output = result['output']
    if hide_empty and result['returncode'] is None:
        output = ''
    if result['returncode'] == NotImplemented:
        if output:
            output = ansi('yellowf') + output + ansi('reset')
    elif result['returncode']:
        if not output:
            output = 'Failed with return code %d' % result['returncode']
        output = ansi('redf') + output + ansi('reset')
    elif not result['cmd']:
        if output:
            output = ansi('yellowf') + output + ansi('reset')
    if output or not hide_empty:
        client = result['client']
        command = result['command']
        print(
            ansi('bluef') + '=== ' +
            ansi('boldon') + command.real_path + ansi('boldoff') +
            ' (' + client.__class__.type + ') ===' + ansi('reset'),
            file=stdout)
    if result['returncode']:
        if output:
            try:
                print(output, file=stdout)
            except UnicodeEncodeError:
                print(
                    output.encode(sys.getdefaultencoding(), 'replace'),
                    file=stdout)
    else:
        print('Valid', file=stdout)

def output_results(results, output_handler=output_result, hide_empty=False):
    # output results in alphabetic order
    path_to_idx = {
        result['command'].real_path: i for i, result in enumerate(results)}
    idxs_in_order = [path_to_idx[path] for path in sorted(path_to_idx.keys())]
    for i in idxs_in_order:
        output_handler(results[i], hide_empty=hide_empty)


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)

    print('Validating format...')

    parser = get_parser()
    add_common_arguments(
        parser, skip_hide_empty=True, skip_nested=True, single_path=True)
    args = parser.parse_args(args)
    try:
        repos = get_repositories(args.input)
    except RuntimeError as e:
        print(ansi('redf') + str(e) + ansi('reset'), file=sys.stderr)
        return 1

    print('Format validation succeeded!')
    print('Validating endpoints...')

    jobs = generate_jobs(repos, args)

    results = execute_jobs(
        jobs, number_of_workers=args.workers,
        debug_jobs=args.debug)
    output_results(results)

    any_error = any(r['returncode'] for r in results)

    if any_error:
        print('An error was encountered while validating an endpoint.', file=sys.stderr)
        return 1
    else:
        print('Endpoint validation succeeded!')
        return 0


if __name__ == '__main__':
    sys.exit(main())
