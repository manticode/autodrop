import pathlib
import unittest
import autodrop


class DirectoryTests(unittest.TestCase):
    def test_get_dir_name(self):
        self.subject_directory = pathlib.Path('/aaa/bbb/my top level Season 7 1080p x264/eee.tmp')
        self.subject_response = autodrop.get_directory_name(self.subject_directory)
        self.assertEqual('my top level Season 7', self.subject_response)


if __name__ == '__main__':
    unittest.main()
