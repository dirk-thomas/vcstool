vcstool_clients = []

try:
    from .bzr import BzrClient
    vcstool_clients.append(BzrClient)
except ImportError:
    pass

try:
    from .git import GitClient
    vcstool_clients.append(GitClient)
except ImportError:
    pass

try:
    from .hg import HgClient
    vcstool_clients.append(HgClient)
except ImportError:
    pass

try:
    from .svn import SvnClient
    vcstool_clients.append(SvnClient)
except ImportError:
    pass

try:
    from .tar import TarClient
    vcstool_clients.append(TarClient)
except ImportError:
    pass

try:
    from .zip import ZipClient
    vcstool_clients.append(ZipClient)
except ImportError:
    pass

_client_types = [c.type for c in vcstool_clients]
if len(_client_types) != len(set(_client_types)):
    raise RuntimeError(
        'Multiple vcs clients share the same type: ' +
        ', '.join(sorted(_client_types)))
