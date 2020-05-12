import logging
import os

from flake8 import configure_logging
from flake8.api.legacy import StyleGuide
from flake8.main.application import Application
from pydocstyle.config import log

log.level = logging.INFO


def test_flake8():
    configure_logging(1)
    argv = [
        '--extend-ignore=' + ','.join([
            'A003', 'D100', 'D101', 'D102', 'D103', 'D104', 'D105', 'D107']),
        '--exclude', 'vcstool/compat/shutil.py',
        '--import-order-style=google']
    style_guide = get_style_guide(argv)
    base_path = os.path.join(os.path.dirname(__file__), '..')
    paths = [
        os.path.join(base_path, 'setup.py'),
        os.path.join(base_path, 'test'),
        os.path.join(base_path, 'vcstool'),
    ]
    scripts_path = os.path.join(base_path, 'scripts')
    for script in os.listdir(scripts_path):
        if script.startswith('.'):
            continue
        paths.append(os.path.join(scripts_path, script))
    report = style_guide.check_files(paths)
    assert report.total_errors == 0, \
        'Found %d code style warnings' % report.total_errors


def get_style_guide(argv=None):
    # this is a fork of flake8.api.legacy.get_style_guide
    # to allow passing command line argument
    application = Application()
    if hasattr(application, 'parse_preliminary_options'):
        prelim_opts, remaining_args = application.parse_preliminary_options(
            argv)
        from flake8 import configure_logging
        configure_logging(prelim_opts.verbose, prelim_opts.output_file)
        from flake8.options import config
        config_finder = config.ConfigFileFinder(
            application.program, prelim_opts.append_config,
            config_file=prelim_opts.config,
            ignore_config_files=prelim_opts.isolated)
        application.find_plugins(config_finder)
        application.register_plugin_options()
        application.parse_configuration_and_cli(config_finder, remaining_args)
    else:
        application.parse_preliminary_options_and_args([])
        application.make_config_finder()
        application.find_plugins()
        application.register_plugin_options()
        application.parse_configuration_and_cli(argv)
    application.make_formatter()
    application.make_guide()
    application.make_file_checker_manager()
    return StyleGuide(application)


if __name__ == '__main__':
    test_flake8()
