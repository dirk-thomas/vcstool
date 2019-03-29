from __future__ import print_function

import sys

from vcstool.commands import import_
from vcstool.executor import ansi
from vcstool.streams import set_streams

from .command import add_common_arguments
from .command import Command


class ValidateCommand(Command):

    command = 'validate'
    help = 'Validate the repository list file'

    def __init__(self, args, url, version=None, recursive=False):
        super(ValidateCommand, self).__init__(args)
        self.url = url
        self.version = version
        self.force = args.force
        self.retry = args.retry
        self.recursive = recursive


def main(args=None, stdout=None, stderr=None):
    set_streams(stdout=stdout, stderr=stderr)

    parser = import_.get_parser()
    add_common_arguments(
        parser, skip_hide_empty=True, skip_nested=True, single_path=True,
        path_help='Base path to clone repositories to')
    args = parser.parse_args(args)
    try:
        import_.get_repositories(args.input)
    except RuntimeError as e:
        print(ansi('redf') + str(e) + ansi('reset'), file=sys.stderr)
        return 1

    print('Validation succeeded!', file=sys.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(main())
