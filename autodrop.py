#!/usr/bin/env python3

"""" Script to automatically upload file on download completion. """

__author__ = "manticode"
__version__ = "0.1.2"

import argparse
import configparser
import os
import subprocess
import tarfile
import tempfile
import rarfile
from pathlib import Path

MEDIA_EXTENSIONS = ['mkv', 'mp4', 'mpeg4', 'avi', 'wmv', 'mov']
ARCHIVE_EXTENSIONS = ['tar', 'zip', 'rar']
SAMPLE_REGEX = '[Ss]ample'
STAGING_DIR = '/home/rtorrent/staging'
SSH_KEYFILE = '/home/rtorrent/.ssh/bigbox'
RSYNC_PATH = '/usr/bin/rsync'
RSYNC_DST_USER = 'serviio'
RSYNC_DST_HOST = 'my.media.server.ip'
RSYNC_DST_PATH = '/mnt/media/incoming/'
RSYNC_OPTIONS = f'-az -e "ssh -p 9022 -i {SSH_KEYFILE}"'


def import_config(**kwargs):
    def set_config_vars():
        print('set config vars')
        global MEDIA_EXTENSIONS
        global ARCHIVE_EXTENSIONS
        global SAMPLE_REGEX
        global STAGING_DIR
        global SSH_KEYFILE
        global RSYNC_PATH
        global RSYNC_DST_USER
        global RSYNC_DST_HOST
        global RSYNC_DST_PATH
        global RSYNC_OPTIONS
        MEDIA_EXTENSIONS = config['autodrop']['MEDIA_EXTENSIONS']
        ARCHIVE_EXTENSIONS = config['autodrop']['ARCHIVE_EXTENSIONS']
        SAMPLE_REGEX = config['autodrop']['SAMPLE_REGEX']
        STAGING_DIR = config['autodrop']['STAGING_DIR']
        SSH_KEYFILE = config['autodrop']['SSH_KEYFILE']
        RSYNC_PATH = config['autodrop']['RSYNC_PATH']
        RSYNC_DST_USER = config['autodrop']['RSYNC_DST_USER']
        RSYNC_DST_HOST = config['autodrop']['RSYNC_DST_HOST']
        RSYNC_DST_PATH = config['autodrop']['RSYNC_DST_PATH']
        RSYNC_OPTIONS = config['autodrop']['RSYNC_OPTIONS']

    config = configparser.ConfigParser()
    if 'config_file' in kwargs.keys():
        print('config file in kwargs')
        if config.read(kwargs['config_file']):
            print(f'config file received: {kwargs["config_file"]}')
            set_config_vars()
        else:
            print('unable to read config')
    else:
        try:
            config.read(Path.home() / '/.autodrop.conf')
            set_config_vars()
        except configparser.Error as e:
            print(f'error due to {e}')


class FilePack:
    """ File or group of files (folder) to be prepared for upload. """

    def __init__(self, filepath):
        self.filename = filepath
        self.media_filename = None
        self.media_archive = None
        self.sample_filename = filepath + 'sample'
        self.singleton = self._check_singleton()
        self.is_tarred = self._check_tarball()
        self.has_sample = self._check_sample()

    def __call__(self):
        return self.filename

    def _check_sample(self):
        """ Return True if media pack contains a Sample media file. """
        if 'sample' in self.filename:
            self.has_sample = True
            return True
        else:
            return False

    def _check_tarball(self):
        """ Return True if file is in an archive file (rar or tar etc). """
        if self.singleton is False:
            for file in os.listdir(self.filename):
                file_extension = file.split('.')[-1]
                if file_extension in ARCHIVE_EXTENSIONS:
                    self.media_archive = Path(self.filename) / file
                    return True
                else:
                    pass
        else:
            return False

    def _check_singleton(self):
        if os.path.isdir(self.filename):
            return False
        else:
            return True


def identify_media(file_group):
    """ Identify files to prepare.
        The files will be identified by media type (mkv, mp4, wmv, avi and mechanism in place to identify sample file.
    """
    pass


def extract_media(media_archive_file, temp_dir):
    """ Extract media from rar. """
    rar_handle = rarfile.RarFile(media_archive_file.media_archive)
    for file in rar_handle.infolist():
        print(file.filename, file.file_size)
        if 'mkv' in file.filename:
            print('MKV found: ', file.filename)
            try:
                rar_handle.extract(file, path=temp_dir.name)
                if rar_handle.strerror() is None:
                    media_archive_file.media_filename = str(Path(temp_dir.name) / file.filename)
                elif rar_handle.strerror() is not None:
                    print(f'strerror: {rar_handle.strerror()}')
            except PermissionError:
                print('unable to extract to specified directory')
        else:
            print('no mkv here')
    print('extract func complete')


def extract_media_tar(media_archive_file):
    """ Extract file from compressed archive. """
    print('about to extract...', media_archive_file.media_archive)
    if tarfile.is_tarfile(media_archive_file.media_archive):
        print('extracting...:', media_archive_file.media_archive)
        tar = tarfile.open(name=media_archive_file.media_archive, mode='r')
        print('tar object created')
        print('tar.name')
        tar.extractall(path=STAGING_DIR)
    print('did not extract')
    pass


def upload_media(file_group):
    """ To upload file to endpoint using rsync. Ensure lockfile to avoid overrunning. """
    rsync_exec = f'{RSYNC_PATH} {RSYNC_OPTIONS} "{file_group}" ' \
                 f'{RSYNC_DST_USER}@{RSYNC_DST_HOST}:"{RSYNC_DST_PATH}"'
    try:
        rsync_ran = subprocess.run(rsync_exec, check=True, shell=True)
        if rsync_ran.returncode == 0:
            return True
        elif rsync_ran.returncode == 35:
            print('Unable to connect')
            return False
        else:
            print(f'Something else went wrong executing rsync\n Return code: {str(rsync_ran.returncode)}')
            return False

    except subprocess.CalledProcessError as e:
        print("Error uploading...")
        print('CMD ran was: ', e.cmd)
        return False


def cli_args():
    parser = argparse.ArgumentParser(description='File to prepare and send.')
    parser.add_argument('filename', type=str, help='the filename and path to send')
    parser.add_argument('--config', type=str, help='path to configuration file')
    return parser.parse_args()


def media_journey(file_group):
    if not file_group.has_sample and file_group.singleton:
        # TODO add check for files in folder but not archived
        if upload_media(file_group.filename):
            print('successfully uploaded media')
        else:
            print('media did not upload. Cleaning up.')
            # TODO add cleanup method
    elif file_group.media_archive:
        print('need to unpack...')
        temp_dir = tempfile.TemporaryDirectory(dir=STAGING_DIR)
        extract_media(file_group, temp_dir)
        if upload_media(file_group.media_filename):
            print('successfully uploaded media')
        else:
            print('media did not upload. Cleaning up.')
            # TODO add cleanup method
        pass


if __name__ == '__main__':
    args = cli_args()
    import_config(config_file=args.config)
    media_group_name = args.filename
    media = FilePack(media_group_name)
    media_journey(media)
