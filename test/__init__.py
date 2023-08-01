import configparser
import pathlib
import unittest

import pyfakefs.pytest_tests.pytest_doctest_test

import autodrop
import os
import unittest.mock
from unittest.mock import Mock, patch
from pathlib import Path

# from unittest.mock import Mock
from pyfakefs import fake_filesystem_unittest


class DirectoryTests(fake_filesystem_unittest.TestCase):
    def setUp(self):
        print('setting up')
        self.setUpPyfakefs()
        os.makedirs('/tmp/downloads')
        self.config = autodrop.import_config()
        print(self.config)
        print(self.config['autodrop'])
        print(self.config['autodrop']['MEDIA_EXTENSIONS'])
        print('done setting up')

    def test_get_dir_name(self):
        subject_directory = pathlib.Path('/aaa/bbb/my top level Season 7 1080p x264/eee.tmp')
        subject_response = autodrop.get_directory_name(subject_directory)
        self.assertEqual('my top level Season 7', subject_response)

    def test_singleton(self):
        test_filename = '/tmp/downloads/mediafile.mkv'
        with open(test_filename, 'w') as file:
            file.write('test data')
        for other_test_media in range(5):
            with open(f'/tmp/downloads/another_file_{other_test_media}.mkv', 'w') as file:
                file.write('test data')
        test_object = autodrop.FilePack('/tmp/downloads/mediafile.mkv', self.config['autodrop']['MEDIA_EXTENSIONS'])
        self.assertEqual(test_object.filename, test_filename)

    def test_single_media(self):
        test_dir = '/tmp/downloads/single media dir'
        os.makedirs(test_dir)
        with open('/tmp/downloads/single media dir/mediafile.mkv', 'w') as file:
            file.write('test data')
        test_object = autodrop.FilePack(test_dir, self.config['autodrop']['MEDIA_EXTENSIONS'])
        self.assertEqual([pathlib.Path('/tmp/downloads/single media dir/mediafile.mkv')], test_object.ready_media)

    def test_sample_media(self):
        os.makedirs('/tmp/downloads/sample media dir')
        test_dir = '/tmp/downloads/sample media dir'
        with open(test_dir + '/mediafile.mkv', 'w') as file:
            file.write('test data')
        with open(test_dir + '/mediafile sample.mkv', 'w') as file:
            file.write('test data')
        test_object = autodrop.FilePack(test_dir, self.config['autodrop']['MEDIA_EXTENSIONS'])
        self.assertEqual([pathlib.Path('/tmp/downloads/sample media dir/mediafile.mkv')], test_object.ready_media)

    def test_multiple_media(self):
        os.makedirs('/tmp/downloads/multiple media dir')
        test_dir = '/tmp/downloads/multiple media dir'
        for episode in range(0, 10):
            with open(f'/tmp/downloads/multiple media dir/media s01e{episode}.mkv', 'w') as file:
                file.write('test data')
        test_object = autodrop.FilePack(test_dir, self.config['autodrop']['MEDIA_EXTENSIONS'])
        self.assertEqual([pathlib.Path(f'{test_dir}/media s01e{x}.mkv') for x in range(0, 10)], test_object.ready_media)

    def test_rar_package(self):
        test_dir = '/tmp/downloads/rar media dir'
        os.makedirs(test_dir)
        for rar_suffix in ['rar'] + [f'r{y:02d}' for y in range(0, 10)]:
            with open(f'{test_dir}/media file.{rar_suffix}', 'w') as file:
                file.write('test data')
        test_object = autodrop.FilePack(test_dir, self.config['autodrop']['MEDIA_EXTENSIONS'])
        self.assertTrue(test_object.media_archive)


class TestMail(unittest.TestCase):
    """ TODO Clean up debug print statements and config object being passed through to function. """
    def setUp(self):
        self.conf = configparser.ConfigParser()

        self.conf.add_section('autodrop')
        self.config = self.conf['autodrop']
        self.conf.set('autodrop', 'NOTIFICATION_EMAIL_FROM', 'test@test.com')
        self.conf.set('autodrop', 'NOTIFICATION_EMAIL_TO', 'test-recipient@example.net')
        #self.config = autodrop.import_config()
        print('Done setting up')

    def test_send_mock_mail(self):
        print(self.conf.get('autodrop', 'NOTIFICATION_EMAIL_FROM'))
        print(self.conf.get('autodrop', 'NOTIFICATION_EMAIL_TO'))
        print(self.conf['autodrop'])
        with patch('smtplib.SMTP') as mock_smtp:
            test_filename = Path('/abc/def/ghi/Test Mock Movie').name
            #autodrop.NOTIFICATION_EMAIL_FROM = 'autodrop-notify@example.com'
            #autodrop.NOTIFICATION_EMAIL_TO = 'test-recipient@example.net'
            test_send = autodrop.send_mail_notification(test_filename, self.conf['autodrop'])
            print(mock_smtp.mock_calls)
            self.assertFalse(test_send)


class TestUpload(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        os.makedirs('/tmp/downloads')
        self.config = autodrop.import_config()

    def test_rsync_upload(self):
        with patch('subprocess.run') as mock_subprocess:
            print(mock_subprocess)
            print(mock_subprocess.return_value)
            print(mock_subprocess.mock_calls)
            test_filename = '/tmp/downloads/fileundertest.mkv'
            with open(test_filename, 'w') as test_file:
                test_file.write('test data test data')
            for other_test_media in range(5):
                with open(f'/tmp/downloads/another_file_{other_test_media}.mkv', 'w') as test_file:
                    test_file.write('test data')
            test_object = autodrop.FilePack('/tmp/downloads/fileundertest.mkv',
                                            self.config['autodrop']['MEDIA_EXTENSIONS'])
            print(test_object.filename)
            print(test_object.ready_media)
            print(test_object.singleton)
            self.assertEqual(test_object.filename, test_filename)

    def test_rsync_upload_no_mock(self):
        rsync_params = {"rsync_path": pathlib.Path('/usr/bin/rsync'),
                        "rsync_options": '-h',
                        "rsync_dst_host": 'host.test.net',
                        "rsync_dst_path": '/tmp/dst_path/',
                        "rsync_dst_user": 'test_user'}

        test_filename = '/tmp/downloads/fileundertest.mkv'
        with open(test_filename, 'w') as test_file:
            test_file.write('test data test data')
        test_object = autodrop.FilePack(test_filename, self.config['autodrop']['MEDIA_EXTENSIONS'])

        with patch('subprocess.run') as subprocess:
            subprocess.return_value.returncode = 0
            autodrop.upload_media(test_object.ready_media, rsync_params)


class TestIfMovieOrSeries(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        os.makedirs('/tmp/downloads')
        self.config = autodrop.import_config()
        print(self.config)

    def test_is_movie_singleton(self):
        # Check if S01E01 and Season 1 Episode 1 is missing, and terminate on 720p or 1080p
        test_sample = autodrop.FilePack(
            '/tmp/downloads/Some.Movie.2021.1080p.SOMETHING+5.1.H.264.mkv',
            self.config['autodrop']['MEDIA_EXTENSIONS'])
        test_template = 'movie'
        self.assertEqual(test_sample.video_type, test_template)

    def test_is_movie_dir(self):
        # Check if S01E01 and Season 1 Episode 1 is missing, and terminate on 720p or 1080p
        test_sample = autodrop.FilePack(
            '/tmp/downloads/Some.Movie.2021.1080p.SOMETHING+5.1.H.264/Some.Movie.2021.1080p.SOMETHING+5.1.H.264.mkv',
            self.config['autodrop']['MEDIA_EXTENSIONS'])
        test_template = 'movie'
        self.assertEqual(test_sample.video_type, test_template)

    def test_is_tv_SnEn_singleton(self):
        # Check against S01E01 format and terminate on that.
        test_sample = autodrop.FilePack('/tmp/downloads/Single.Media.S03E04.mkv',
                                        self.config['autodrop']['MEDIA_EXTENSIONS'])
        print(test_sample.video_type)
        self.assertEqual(test_sample.video_type, 'tv')

    def test_is_tv_SnEn_dir(self):
        # Check against S01E01 format and terminate on that.
        test_sample = autodrop.FilePack('/tmp/downloads/Single.Media.S03E04/single.media.s03e04.1080p.mkv',
                                        self.config['autodrop']['MEDIA_EXTENSIONS'])
        print(test_sample.video_type)
        self.assertEqual(test_sample.video_type, 'tv')

    def test_is_tv_Season_n(self):
        # Check against Season 1 Episode 1 format and terminate on that. More useful for packs than singletons.
        test_sample = autodrop.FilePack('/tmp/downloads/Single.Media.S03E04.mkv',
                                        self.config['autodrop']['MEDIA_EXTENSIONS'])
        print(test_sample.video_type)
        self.assertEqual(test_sample.video_type, 'tv')

    def test_something_invalid(self):
        test_sample = autodrop.FilePack('/tmp/downloads/something else',
                                        self.config['autodrop']['MEDIA_EXTENSIONS'])
        with self.assertRaises(AttributeError):
            test_sample.video_type


class RemoteDirNameTests(unittest.TestCase):
    def test_get_dir_name_from_dotted_single_episode(self):
        test_sample = pathlib.Path('/tmp/downloads/Multiple.Media.S02E03/Multiple.Media.S02E03.mkv')
        test_template = 'Multiple Media Season 2'
        print(autodrop.get_directory_name(test_sample))
        self.assertEqual(test_template, autodrop.get_directory_name(test_sample))

    def test_get_dir_name_from_space_single_episode(self):
        test_sample = pathlib.Path('/tmp/downloads/Multiple Media S02E03/Multiple Media S02E03.mkv')
        test_template = 'Multiple Media Season 2'
        print(autodrop.get_directory_name(test_sample))
        self.assertEqual(test_template, autodrop.get_directory_name(test_sample))

    def test_get_dir_name_with_prefix_single_episode(self):
        test_sample = pathlib.Path('/tmp/downloads/[Something]Multiple.Media.S02E03/multiple.media.s02e03.mkv')
        test_template = 'Multiple Media Season 2'
        print(autodrop.get_directory_name(test_sample))
        self.assertEqual(test_template, autodrop.get_directory_name(test_sample))

    def test_get_dir_name_with_numbers_single_episode(self):
        test_sample = pathlib.Path('/tmp/downloads/Multiple.Media.2021.S02E03/media.mkv')
        test_template = 'Multiple Media 2021 Season 2'
        print(autodrop.get_directory_name(test_sample))
        self.assertEqual(test_template, autodrop.get_directory_name(test_sample))

    @unittest.skip
    def test_get_dir_name_from_dotted_movie(self):
        test_sample = pathlib.Path('/tmp/downloads/Some.Movie.2021.1080p.SOMETHING+5.1.H.264/Some.Movie.2021.1080p.SOMETHING+5.1.H.264.mkv')
        test_template = 'Some Movie 2021'
        print(autodrop.get_directory_name(test_sample))
        self.assertEqual(test_template, autodrop.get_directory_name(test_sample))

    @unittest.skip
    def test_get_dir_name_from_space_movie(self):
        test_sample = Path('/tmp/downloads/Some Movie 2021 720p XYZ 5.1 H.264/Some Movie 2021 720p XYZ 5.1 H.264.mkv')
        test_template = 'Some Movie'
        print(autodrop.get_directory_name(test_sample))
        self.assertEqual(test_template, autodrop.get_directory_name(test_sample))

    def test_get_dir_name_with_prefix_movie(self):
        pass

    def test_sample_name_with_numbers_movie(self):\
        pass

    def get_dir_name_from_dotted_pack(self):
        pass

    def get_dir_name_from_space_pack(self):
        pass


if __name__ == '__main__':
    unittest.main()
