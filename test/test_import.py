# Copyright 2020 Rover Robotics c/o Dan Rose
# Licensed under the Apache License, Version 2.0
import base64

from vcstool.commands import import_
from urllib.parse import urlencode

REPOS_YAML = """
repositories:
  vcstool:
    type: git
    url: https://github.com/dirk-thomas/vcstool.git
    version: master
"""


def test_import_file(tmp_path):
    repos_file = tmp_path / 'repos.yml'
    repos_file.write_text(REPOS_YAML)
    import_.main(args=[str(tmp_path), '--input', str(repos_file)])
    assert (tmp_path / 'vcstool'/'.git').is_dir()


def test_import_file_url(tmp_path):
    repos_file = tmp_path / 'repos.yml'
    repos_file.write_text(REPOS_YAML)
    repos_url = 'file:/' + str(repos_file)
    import_.main(args=[str(tmp_path), '--input', str(repos_url)])
    assert (tmp_path / 'vcstool'/'.git').is_dir()


REPOS_DATA_URL = (
    "data:text/x-yaml;charset=utf-8,"
    "repositories%3A%0D%0A%20%20vcstool%3A%0D%0A%20%20%20%20type%3A"
    "%20git%0D%0A%20%20%20%20url%3A%20https%3A%2F%2Fgithub.com%2Fdirk-thomas"
    "%2Fvcstool.git%0D%0A%20%20%20%20version%3A%20master"
)

def test_import_data_url(tmp_path):
    data_url = b'data:text/x-yaml;base64,'+base64.b64encode(REPOS_YAML)
    import_.main(args=[tmp_path, '--input', data_url])
    assert (tmp_path / 'vcstool'/'.git').is_dir()
