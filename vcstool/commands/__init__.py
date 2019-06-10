from .branch import BranchCommand
from .custom import CustomCommand
from .diff import DiffCommand
from .export import ExportCommand
from .import_ import ImportCommand
from .log import LogCommand
from .pull import PullCommand
from .push import PushCommand
from .remotes import RemotesCommand
from .status import StatusCommand
from .validate import ValidateCommand

vcstool_commands = []
vcstool_commands.append(BranchCommand)
vcstool_commands.append(CustomCommand)
vcstool_commands.append(DiffCommand)
vcstool_commands.append(ExportCommand)
vcstool_commands.append(ImportCommand)
vcstool_commands.append(LogCommand)
vcstool_commands.append(PullCommand)
vcstool_commands.append(PushCommand)
vcstool_commands.append(RemotesCommand)
vcstool_commands.append(StatusCommand)
vcstool_commands.append(ValidateCommand)

_commands = [c.command for c in vcstool_commands]
if len(_commands) != len(set(_commands)):
    raise RuntimeError(
        'Multiple commands share the same command name: ' +
        ', '.join(sorted(_commands)))
