#!/usr/bin/env python3

"""" Script to automatically upload file to media server on download completion. """

__author__ = "manticode"
__version__ = "0.1.4"

import argparse
import configparser
import os
import re
import smtplib
import subprocess
import sys
import tarfile
import tempfile
import rarfile
import uuid
from pathlib import Path


def import_config(**kwargs):
    def set_config_vars():
        print('set config vars')
        try:
            config_options = config['autodrop']
        except KeyError as e:
            config.add_section('autodrop')
            config_options = config['autodrop']
        config_options.setdefault('MEDIA_EXTENSIONS', str(['mkv', 'mp4', 'mpeg4', 'avi', 'wmv', 'mov']))
        config_options.setdefault('ARCHIVE_EXTENSIONS', str(['tar', 'zip', 'rar', 'bzip2']))
        config_options.setdefault('SAMPLE_REGEX', str('[Ss]ample'))
        config_options.setdefault('STAGING_DIR', '/tmp')
        # SSH_KEYFILE = config['autodrop']['SSH_KEYFILE']
        config_options.setdefault('RSYNC_PATH', str(subprocess.run(['which', 'rsync']).stdout))

    config = configparser.ConfigParser()
    if 'config_file' in kwargs.keys():
        if kwargs['config_file'] is not None:
            try:
                if config.read(kwargs['config_file']) is not None:
                    set_config_vars()
                else:
                    print('unable to read config')
                    sys.exit()
            except TypeError:
                sys.exit()
        else:
            try:
                config.read(Path.home() / '.autodrop.conf')
                set_config_vars()
            except configparser.Error as e:
                print(f'error due to {e}')
    else:
        set_config_vars()
    return config


class FilePack:
    """ File or group of files (folder) to be prepared for upload. """

    def __init__(self, filepath, media_extensions, **kwargs):
        self.filename = filepath
        self.media_extensions = media_extensions

        try:
            self.sample_regex = kwargs['SAMPLE_REGEX']
        except KeyError:
            self.sample_regex = '[Ss]ample'

        self.singleton = self._check_singleton()
        self._check_media()
        self.media_archive = None
        self.sample_filename = filepath + 'sample'
        self.has_sample = self._check_sample()
        self._video_type()

        try:
            self.archive_extensions = kwargs['archive_extensions']
        except KeyError:
            self.archive_extensions = ['rar']

        self.is_tarred = self._check_tarball()


    def __call__(self):
        return self.filename

    def _check_media(self):
        self.ready_media = []
        if self.singleton is False:
            media_candidates = []
            for file in os.listdir(self.filename):
                file_extension = file.split('.')[-1]
                if file_extension in self.media_extensions:
                    media_candidates.append(file)
                else:
                    pass
            if len(media_candidates) == 1:
                self.ready_media.append(Path(self.filename) / media_candidates.pop())
            elif len(media_candidates) > 1:
                for file in media_candidates:
                    # TODO this needs to be a bit smarter...
                    if re.search(self.sample_regex, file):
                        pass
                    else:
                        self.ready_media.append(Path(self.filename) / file)
        elif self.singleton:
            self.ready_media.append(Path(self.filename))

    def _video_type(self):
        if re.search('[Ss][0-9]{2}[Ee][0-9]{2}', self.filename):
            self.video_type = 'tv'
        elif re.search('[Ss]eason [0-9]{1,3}', self.filename):
            self.video_type = 'tv'
        elif re.search('(1080p|720p|480p)', self.filename):
            self.video_type = 'movie'

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
                if file_extension in self.archive_extensions:
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
                    media_archive_file.ready_media.append(Path(temp_dir.name) / file.filename)
                elif rar_handle.strerror() is not None:
                    print(f'strerror: {rar_handle.strerror()}')
            except PermissionError:
                print('unable to extract to specified directory')
        else:
            print('no mkv here')


def upload_media(file_group, rsync_args):
    """ To upload file to endpoint using rsync. """
    upload_file_string = ' '.join(['"' + str(file) + '"' for file in file_group])
    print(upload_file_string)
    rsync_exec = f'{rsync_args["rsync_path"]} {rsync_args["rsync_options"]} {upload_file_string} ' \
                 f'{rsync_args["rsync_dst_user"]}@{rsync_args["rsync_dst_host"]}:"{rsync_args["rsync_dst_path"]}"'
    print(rsync_exec)
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
    parser.add_argument('--dry-run', '-n', action='store_const', const='DRY_RUN', help='dry run - does nothing at the '
                                                                                       'moment')
    return parser.parse_args()


def media_journey(file_group, config_opts, stg_dir):
    config_params = config_opts['autodrop']
    rsync_params = {"rsync_path": config_params.get('RSYNC_PATH'),
                    "rsync_options": config_params.get('RSYNC_OPTIONS'),
                    "rsync_dst_host": config_params.get('RSYNC_DST_HOST'),
                    "rsync_dst_path": config_params.get('RSYNC_DST_PATH'),
                    "rsync_dst_user": config_params.get('RSYNC_DST_USER')}
    if not file_group.has_sample and file_group.singleton:
        transfer_source = file_group.ready_media
        if upload_media(file_group.ready_media, rsync_params):
            send_mail_notification(Path(file_group.filename).name, config_params)
        else:
            print('media did not upload. Cleaning up.')
            # TODO add cleanup method
    elif file_group.media_archive:
        temp_dir = tempfile.TemporaryDirectory(dir=stg_dir)
        extract_media(file_group, temp_dir)
        if upload_media(file_group.ready_media, rsync_params):
            send_mail_notification(Path(file_group.filename).name, config_params)
        else:
            print('media did not upload. Cleaning up.')
            sys.exit()
        pass
    elif file_group.ready_media and not file_group.has_sample and not file_group.singleton:
        if upload_media(file_group.ready_media, rsync_params):
            print('media uploaded')
            send_mail_notification(Path(file_group.filename).name, config_params)
        else:
            print('media not uploaded.')
    print('upload attempt complete')


def is_movie_or_tv(media_pack):
    # if has SnnEnn in name then true
    # if has Season n Episode n in name then true
    # if has 1080p or 720p or 480p in name then true
    # else is not a movie or tv episode/season
    # this should probably be an object method
    pass


def get_directory_name(media_pack):
    directory_name = re.search('^(?:\\[.*?])?(.*?)(?:(?:[Ss]|[Ss]eason[. ])([0-9]{1,3})).*', media_pack.parent.name)
    if directory_name:
        if directory_name.group(2):
            return directory_name.group(1).replace('.', ' ').strip() + ' Season ' + directory_name.group(2).lstrip('0')
        else:
            return directory_name.group(1).replace('.', ' ').strip()
    else:
        return 'FAIL'


def send_mail_notification(filename, config_opts):
    """ Only local running SMTP server supported currently. """
    msg = f'From: "Autodrop Notify" <{config_opts.get("EMAIL_FROM")}>\n' \
          f'To: <{config_opts.get("EMAIL_TO")}>\n' \
          f'Subject: Media transfer complete for {filename}\n' \
          f'Message-ID: <{uuid.uuid4()}@{config_opts.get("EMAIL_FROM").split("@")[1]}>\n' \
          f'X-autodrop-version: {__version__}\n\n' \
          f'Hi,\n\n' \
          f'Transfer of {filename} complete.\n'
    server = smtplib.SMTP('localhost')
    server.set_debuglevel(False)
    server.sendmail(f'{config_opts.get("EMAIL_FROM")}', f'{config_opts.get("EMAIL_TO")}', msg)
    server.quit()


if __name__ == '__main__':
    args = cli_args()
    config = import_config(config_file=args.config)
    media_group_name = args.filename
    staging_dir = Path(config['autodrop']['STAGING_DIR'])
    if not staging_dir.exists():
        staging_dir.mkdir(parents=True, exist_ok=True)
    media = FilePack(media_group_name,
                     config['autodrop']['MEDIA_EXTENSIONS'])
    media_journey(media, config, staging_dir)
