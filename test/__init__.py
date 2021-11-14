import pathlib
import unittest

import pyfakefs.pytest_tests.pytest_doctest_test

import autodrop
import os
# from unittest.mock import Mock
from pyfakefs import fake_filesystem_unittest


class DirectoryTests(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        os.makedirs('/tmp/downloads')

    def test_get_dir_name(self):
        self.subject_directory = pathlib.Path('/aaa/bbb/my top level Season 7 1080p x264/eee.tmp')
        self.subject_response = autodrop.get_directory_name(self.subject_directory)
        self.assertEqual('my top level Season 7', self.subject_response)

    def test_singleton(self):
        with open('/tmp/downloads/mediafile.mkv', 'w') as file:
            file.write('test data')
        self.assertEqual(['mediafile.mkv'], os.listdir('/tmp/downloads/'))

    def test_single_media(self):
        os.makedirs('/tmp/downloads/single media dir')
        with open('/tmp/downloads/single media dir/mediafile.mkv', 'w') as file:
            file.write('test data')
        self.assertEqual(['mediafile.mkv'], os.listdir('/tmp/downloads/single media dir'))

    def test_sample_media(self):
        os.makedirs('/tmp/downloads/sample media dir')
        with open('/tmp/downloads/sample media dir/mediafile.mkv', 'w') as file:
            file.write('test data')
        with open('/tmp/downloads/sample media dir/mediafile sample.mkv', 'w') as file:
            file.write('test data')
        self.assertEqual(['mediafile.mkv', 'mediafile sample.mkv'], os.listdir('/tmp/downloads/sample media dir'))

    def test_multiple_media(self):
        os.makedirs('/tmp/downloads/multiple media dir')
        for episode in range(0, 10):
            with open(f'/tmp/downloads/multiple media dir/media s01e{episode}.mkv', 'w') as file:
                file.write('test data')
        self.assertEqual([f'media s01e{x}.mkv' for x in range(0, 10)], os.listdir('/tmp/downloads/multiple media dir'))

    def test_rar_package(self):
        os.makedirs('/tmp/downloads/rar media dir')
        for rar_suffix in ['rar'] + [f'r{y:02d}' for y in range(0, 5)]:
            with open(f'/tmp/downloads/rar media dir/media file.{rar_suffix}', 'w') as file:
                file.write('test data')
        self.assertEqual(['media file.rar'] + [f'media file.r{y:02d}' for y in range(0, 5)],
                         os.listdir('/tmp/downloads/rar media dir'))


if __name__ == '__main__':
    unittest.main()
