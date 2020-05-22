import os
import shutil
import tempfile
import textwrap
import unittest

try:
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import HTTPError


try:
    from unittest import mock
except ImportError:
    import mock

from vcstool.clients import vcs_base


class TestBase(unittest.TestCase):

    def setUp(self):
        self.default_auth_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.default_auth_dir)
        self.user_auth_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.user_auth_dir)
        self.system_auth_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.system_auth_dir)

        self._previous_home = os.getenv("HOME")
        os.environ["HOME"] = self.default_auth_dir

        patcher = mock.patch(
            'vcstool.clients.vcs_base.appdirs.user_config_dir',
            return_value=self.user_auth_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'vcstool.clients.vcs_base.appdirs.site_config_dir',
            return_value=self.system_auth_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        if self._previous_home:
            os.environ["HOME"] = self._previous_home
        else:
            del os.environ["HOME"]

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    @mock.patch(
        'vcstool.clients.vcs_base._authenticated_urlopen', autospec=True)
    def test_load_url_calls_urlopen(
            self, authenticated_urlopen_mock, urlopen_mock):
        urlopen_read_mock = urlopen_mock.return_value.read

        vcs_base.load_url('example.com', timeout=123)

        urlopen_mock.assert_called_once_with('example.com', timeout=123)
        urlopen_read_mock.assert_called_once_with()
        self.assertFalse(authenticated_urlopen_mock.mock_calls)

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    @mock.patch(
        'vcstool.clients.vcs_base._authenticated_urlopen', autospec=True)
    def test_load_url_calls_authenticated_urlopen(
            self, authenticated_urlopen_mock, urlopen_mock):
        for code in (401, 404):
            urlopen_mock.side_effect = [
                HTTPError(None, code, 'test', None, None)]
            urlopen_read_mock = urlopen_mock.return_value.read

            vcs_base.load_url('example.com', timeout=123)

            urlopen_mock.assert_called_once_with('example.com', timeout=123)
            self.assertFalse(urlopen_read_mock.mock_calls)

            authenticated_urlopen_mock.assert_called_once_with(
                'example.com', retry=2, retry_period=1, timeout=123)

            authenticated_urlopen_mock.reset_mock()
            urlopen_mock.reset_mock()

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    @mock.patch(
        'vcstool.clients.vcs_base._authenticated_urlopen', autospec=True)
    def test_test_url_calls_urlopen(
            self, authenticated_urlopen_mock, urlopen_mock):
        url = 'http://example.com'
        vcs_base.test_url(url, timeout=123)

        class _RequestMatcher(object):
            def __init__(self, test):
                self.test = test

            def __eq__(self, other):
                self.test.assertEqual(other.get_full_url(), url)
                return True

        urlopen_mock.assert_called_once_with(
            _RequestMatcher(self), timeout=123)
        self.assertFalse(authenticated_urlopen_mock.mock_calls)

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    @mock.patch(
        'vcstool.clients.vcs_base._authenticated_urlopen', autospec=True)
    def test_test_url_calls_authenticated_urlopen(
            self, authenticated_urlopen_mock, urlopen_mock):
        for code in (401, 404):
            urlopen_mock.side_effect = [
                HTTPError(None, code, 'test', None, None)]

            url = 'http://example.com'
            vcs_base.test_url(url, timeout=123)

            class _RequestMatcher(object):
                def __init__(self, test):
                    self.test = test

                def __eq__(self, other):
                    self.test.assertEqual(other.get_full_url(), url)
                    return True

            urlopen_mock.assert_called_once_with(
                _RequestMatcher(self), timeout=123)

            authenticated_urlopen_mock.assert_called_once_with(
                _RequestMatcher(self), retry=2, retry_period=1, timeout=123)

            authenticated_urlopen_mock.reset_mock()
            urlopen_mock.reset_mock()

    def test_netrc_open_no_such_file(self):
        try:
            self.assertEqual(vcs_base._authenticated_urlopen(
                'https://example.com'), None)
        except Exception:
            self.fail(
                'The lack of a .netrc file should not result in an exception')

    def test_netrc_file_precedence(self):
        machine = 'example.com'

        default_auth_file_path = os.path.join(self.default_auth_dir, '.netrc')
        user_auth_file_path = os.path.join(
            self.user_auth_dir, vcs_base._AUTHENTICATION_CONFIGURATION_FILE)
        system_auth_file_path = os.path.join(
            self.system_auth_dir, vcs_base._AUTHENTICATION_CONFIGURATION_FILE)

        for path in (
                default_auth_file_path, user_auth_file_path,
                system_auth_file_path):
            _create_netrc_file(path, textwrap.dedent('''\
                machine %s
                password %s
                ''' % (machine, path)))

        credentials = vcs_base._credentials_for_machine(machine)
        self.assertIsNotNone(credentials)
        self.assertEqual(len(credentials), 3)
        self.assertEqual(credentials[2], default_auth_file_path)

        # Remove default auth file and assert that the user auth file is used
        os.unlink(default_auth_file_path)
        credentials = vcs_base._credentials_for_machine(machine)
        self.assertIsNotNone(credentials)
        self.assertEqual(len(credentials), 3)
        self.assertEqual(credentials[2], user_auth_file_path)

        # Remove user auth file and assert that the system auth file is used
        os.unlink(user_auth_file_path)
        credentials = vcs_base._credentials_for_machine(machine)
        self.assertIsNotNone(credentials)
        self.assertEqual(len(credentials), 3)
        self.assertEqual(credentials[2], system_auth_file_path)

        # Remove system auth file and assert that no creds are found
        os.unlink(system_auth_file_path)
        self.assertIsNone(vcs_base._credentials_for_machine(machine))

    def test_netrc_file_skip_errors(self):
        machine = 'example.com'

        default_auth_file_path = os.path.join(self.default_auth_dir, '.netrc')
        user_auth_file_path = os.path.join(
            self.user_auth_dir, vcs_base._AUTHENTICATION_CONFIGURATION_FILE)

        _create_netrc_file(default_auth_file_path, 'skip-me-invalid')

        _create_netrc_file(user_auth_file_path, textwrap.dedent('''\
            machine %s
            password %s
            ''' % (machine, user_auth_file_path)))

        credentials = vcs_base._credentials_for_machine(machine)
        self.assertIsNotNone(credentials)
        self.assertEqual(len(credentials), 3)
        self.assertEqual(credentials[2], user_auth_file_path)

    def test_auth_parts(self):
        user_auth_file_path = os.path.join(
            self.user_auth_dir, vcs_base._AUTHENTICATION_CONFIGURATION_FILE)
        user_auth_file_part_path = os.path.join(
            self.user_auth_dir,
            vcs_base._AUTHENTICATION_CONFIGURATION_PARTS_DIR, 'test.conf')
        os.makedirs(os.path.dirname(user_auth_file_part_path))

        auth_machine = 'auth.example.com'
        parts_machine = 'parts.example.com'

        for path in (user_auth_file_path, user_auth_file_part_path):
            _create_netrc_file(path, textwrap.dedent('''\
                machine %s
                password %s
                ''' % (auth_machine, path)))
        with open(user_auth_file_part_path, 'a') as f:
            f.write('machine %s\n' % parts_machine)
            f.write('password %s\n' % path)

        credentials = vcs_base._credentials_for_machine(auth_machine)
        self.assertIsNotNone(credentials)
        self.assertEqual(len(credentials), 3)
        self.assertEqual(credentials[2], user_auth_file_path)

        credentials = vcs_base._credentials_for_machine(parts_machine)
        self.assertIsNotNone(credentials)
        self.assertEqual(len(credentials), 3)
        self.assertEqual(credentials[2], user_auth_file_part_path)

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    @mock.patch('vcstool.clients.vcs_base.build_opener', autospec=True)
    def test_authenticated_urlopen_basic_auth(
            self, build_opener_mock, urlopen_mock):
        open_mock = build_opener_mock.return_value.open

        machine = 'example.com'
        _create_netrc_file(
            os.path.join(self.default_auth_dir, '.netrc'),
            textwrap.dedent('''\
                machine %s
                login username
                password password
                ''' % machine))

        url = 'https://%s/foo/bar' % machine
        vcs_base._authenticated_urlopen(url)

        self.assertFalse(urlopen_mock.mock_calls)

        class _HTTPBasicAuthHandlerMatcher(object):
            def __init__(self, test):
                self.test = test

            def __eq__(self, other):
                manager = other.passwd
                self.test.assertEqual(
                    manager.find_user_password(None, 'example.com'),
                    ('username', 'password'))
                return True

        class _RequestMatcher(object):
            def __init__(self, test):
                self.test = test

            def __eq__(self, other):
                self.test.assertEqual(other.get_full_url(), url)
                return True

        build_opener_mock.assert_called_once_with(
            _HTTPBasicAuthHandlerMatcher(self))
        open_mock.assert_called_once_with(_RequestMatcher(self), timeout=10)

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    @mock.patch('vcstool.clients.vcs_base.build_opener', autospec=True)
    def test_authenticated_urlopen_token_auth(
            self, build_opener_mock, urlopen_mock):
        machine = 'example.com'
        _create_netrc_file(
            os.path.join(self.default_auth_dir, '.netrc'),
            textwrap.dedent('''\
                machine %s
                password password
                ''' % machine))

        url = 'https://%s/foo/bar' % machine
        vcs_base._authenticated_urlopen(url)

        self.assertFalse(build_opener_mock.mock_calls)

        class _RequestMatcher(object):
            def __init__(self, test):
                self.test = test

            def __eq__(self, other):
                self.test.assertEqual(other.get_full_url(), url)
                self.test.assertEqual(
                    other.get_header('Private-token'), 'password')
                return True

        urlopen_mock.assert_called_once_with(
            _RequestMatcher(self), timeout=10)

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    def test_load_url_retries(self, urlopen_mock):
        urlopen_read_mock = urlopen_mock.return_value.read
        urlopen_mock.side_effect = [
            HTTPError(None, 503, 'test1', None, None),
            HTTPError(None, 503, 'test2', None, None),
            HTTPError(None, 503, 'test3', None, None),
        ]

        with self.assertRaises(HTTPError) as e:
            vcs_base.load_url('example.com')

        self.assertTrue('test3' in str(e.exception))

        self.assertEqual(len(urlopen_mock.mock_calls), 3)
        urlopen_mock.assert_has_calls([
            mock.call('example.com', timeout=10),
            mock.call('example.com', timeout=10),
            mock.call('example.com', timeout=10),
        ])
        self.assertFalse(urlopen_read_mock.mock_calls)

    @mock.patch('vcstool.clients.vcs_base.urlopen', autospec=True)
    def test_load_url_retries_authenticated(self, urlopen_mock):
        urlopen_read_mock = urlopen_mock.return_value.read
        urlopen_mock.side_effect = [
            HTTPError(None, 401, 'test1', None, None),
            HTTPError(None, 503, 'test2', None, None),
            HTTPError(None, 503, 'test3', None, None),
            HTTPError(None, 503, 'test4', None, None),
        ]

        machine = 'example.com'
        _create_netrc_file(
            os.path.join(self.default_auth_dir, '.netrc'),
            textwrap.dedent('''\
                machine %s
                password password
                ''' % machine))

        url = 'https://%s/foo/bar' % machine

        with self.assertRaises(HTTPError) as e:
            vcs_base.load_url(url)

        self.assertTrue('test4' in str(e.exception))

        self.assertEqual(len(urlopen_mock.mock_calls), 4)

        class _RequestMatcher(object):
            def __init__(self, test):
                self.test = test

            def __eq__(self, other):
                self.test.assertEqual(other.get_full_url(), url)
                self.test.assertEqual(
                    other.get_header('Private-token'), 'password')
                return True

        urlopen_mock.assert_has_calls([
            mock.call(url, timeout=10),
            mock.call(_RequestMatcher(self), timeout=10),
            mock.call(_RequestMatcher(self), timeout=10),
            mock.call(_RequestMatcher(self), timeout=10),
        ])
        self.assertFalse(urlopen_read_mock.mock_calls)


def _create_netrc_file(path, contents):
    with open(path, 'w') as f:
        f.write(contents)
    os.chmod(path, 0o600)
