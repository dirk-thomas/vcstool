from __future__ import print_function

import argparse
import sys

from vcstool.clients import vcstool_clients
from vcstool.commands.import_ import get_repositories
from vcstool.executor import ansi
from vcstool.executor import execute_jobs
from vcstool.executor import output_results
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

        client = clients[0](path)
        args.path = None  # expected to be present
        command = ValidateCommand(
            args, repo['url'],
            str(repo['version']) if 'version' in repo else None)
        job = {'client': client, 'command': command}
        jobs.append(job)
    return jobs


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)

    parser = get_parser()
    add_common_arguments(
        parser, skip_nested=True, path_nargs=False)
    args = parser.parse_args(args)
    try:
        repos = get_repositories(args.input)
    except RuntimeError as e:
        print(ansi('redf') + str(e) + ansi('reset'), file=sys.stderr)
        return 1

    jobs = generate_jobs(repos, args)

    results = execute_jobs(
        jobs, show_progress=True, number_of_workers=args.workers,
        debug_jobs=args.debug)

    output_results(results, hide_empty=args.hide_empty)

    any_error = any(r['returncode'] for r in results)
    return 1 if any_error else 0


if __name__ == '__main__':
    sys.exit(main())
