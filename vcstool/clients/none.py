from .vcs_base import VcsClientBase


class NoneClient(VcsClientBase):

    type = 'none'

    def __init__(self, path):
        super(NoneClient, self).__init__(path)
