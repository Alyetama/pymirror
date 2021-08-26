import re
import sys
import unittest
import warnings
from pathlib import Path

import psutil

from pymirror.api_upload import APIUpload
from pymirror.cli import cli
from pymirror.helpers import load_data, kill_firefox_zombies
from pymirror.main import PyMirror
from pymirror.mirroredto import Mirroredto
from pymirror.multiup import MultiUp


class Options:
    remove_config = False


class PyMirrorTests(unittest.TestCase):
    def setUp(self):
        self.foo = Path('foo.txt')
        if not self.foo.exists():
            with open(str(self.foo), 'w') as f:
                f.write('foo\n')

    def tearDown(self):
        self.foo.unlink()
        if Options.remove_config:
            config_file = ['config.ini']
        else:
            config_file = []
        for file in ['geckodriver.log'] + config_file:
            if Path(file).exists():
                Path(file).unlink()

    def _args(self, options):
        sys.argv[1:] = ['-i', str(self.foo)] + options
        return cli()

    @staticmethod
    def _match_regex(regex, string):
        matches = re.finditer(regex, string, re.MULTILINE)
        return matches

    def test_api_upload(self):
        data = load_data()
        api_upload_obj = APIUpload(data, self._args(['--debug']))
        api_upload_links = api_upload_obj.api_uploads()
        self.assertNotEqual(api_upload_links, [])

    def test_mirroredto(self):
        mirroredto_obj = Mirroredto(self._args(['--debug']))
        mirroredto_links = mirroredto_obj.upload()
        self.assertNotEqual(mirroredto_links, [])

    def test_multiup(self):
        mu_obj = MultiUp(self._args(['--debug']))
        mu_links = mu_obj.upload()
        self.assertNotEqual(mu_links, [])

    def test_styling(self):
        data = load_data()
        args = self._args(['--number', '2'])
        test_links = APIUpload(data, args).api_uploads()
        output = PyMirror(args).style_output(test_links[0])
        self.assertIsInstance(output, str)
        regex = [('markdown', r'\-\s\[[^\]]*\]\([^)]*\)'),
                 ('reddit', r'\[[a-zA-Z]+\s\d\]\([^)]*\)')]
        for style, pattern in regex:
            output = PyMirror(self._args(['--debug', '--style',
                                          style])).style_output(test_links)
            matches = self._match_regex(pattern, output)
            self.assertNotEqual(list(matches), [])
        output = PyMirror(self._args(['--debug', '--style',
                                      'list'])).style_output(test_links)
        self.assertIsInstance(output, list)
        self.assertNotEqual(output, [])

    def test_firefox_zombies(self):
        terminated = kill_firefox_zombies()
        for proc in terminated:
            pid_exists = psutil.pid_exists(proc)
            self.assertEqual(pid_exists, False)


if __name__ == '__main__':
    Options.remove_config = True
    warnings.filterwarnings(action='ignore', category=ResourceWarning)
    unittest.main()
