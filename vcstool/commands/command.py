import os


class Command(object):

    def __init__(self, args):
        self.debug = args.debug
        self.path = args.path
        self.repos = args.repos

    def get_command_line(self, client):
        raise NotImplementedError()


def add_common_arguments(parser):
    group = parser.add_argument_group('Common parameters')
    group.add_argument('--debug', action='store_true', default=False, help='Show debug messages')
    group.add_argument('--repos', action='store_true', default=False, help='List repositories which the command operates on')
    group.add_argument('path', nargs='?', default=os.curdir, help='Base path to look for repositories')
