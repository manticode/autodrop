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
        test_filename = '/tmp/downloads/mediafile.mkv'
        with open(test_filename, 'w') as file:
            file.write('test data')
        test_object = autodrop.FilePack('/tmp/downloads/mediafile.mkv')
        self.assertEqual(test_object.filename, test_filename)

    def test_single_media(self):
        test_dir = '/tmp/downloads/single media dir'
        os.makedirs(test_dir)
        with open('/tmp/downloads/single media dir/mediafile.mkv', 'w') as file:
            file.write('test data')
        test_object = autodrop.FilePack(test_dir)
        self.assertEqual([pathlib.Path('/tmp/downloads/single media dir/mediafile.mkv')], test_object.ready_media)

    def test_sample_media(self):
        os.makedirs('/tmp/downloads/sample media dir')
        test_dir = '/tmp/downloads/sample media dir'
        with open(test_dir + '/mediafile.mkv', 'w') as file:
            file.write('test data')
        with open(test_dir + '/mediafile sample.mkv', 'w') as file:
            file.write('test data')
        test_object = autodrop.FilePack(test_dir)
        print(test_object.ready_media)
        self.assertEqual([pathlib.Path('/tmp/downloads/sample media dir/mediafile.mkv')], test_object.ready_media)

    def test_multiple_media(self):
        os.makedirs('/tmp/downloads/multiple media dir')
        test_dir = '/tmp/downloads/multiple media dir'
        for episode in range(0, 10):
            with open(f'/tmp/downloads/multiple media dir/media s01e{episode}.mkv', 'w') as file:
                file.write('test data')
        test_object = autodrop.FilePack(test_dir)
        self.assertEqual([pathlib.Path(f'{test_dir}/media s01e{x}.mkv') for x in range(0, 10)], test_object.ready_media)

    def test_rar_package(self):
        test_dir = '/tmp/downloads/rar media dir'
        os.makedirs(test_dir)
        for rar_suffix in ['rar'] + [f'r{y:02d}' for y in range(0, 10)]:
            with open(f'{test_dir}/media file.{rar_suffix}', 'w') as file:
                file.write('test data')
        test_object = autodrop.FilePack(test_dir)
        self.assertTrue(test_object.media_archive)


if __name__ == '__main__':
    unittest.main()
