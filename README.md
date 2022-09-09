# Autodrop
MIT License

Script to automatically upload completed torrents to another location, such as from a seedbox to a media server.

### Requires:
* CentOS or Debian or suitable Linux operating sytem
* **Python 3.8+** (may work on older Python 3 versions, but this project was created with Python 3.8)
* **rtorrent** installed and configured
* **unrar** and **rsync** installed
* static IP address or dynamic DNS

### Usage
* Configure the global variables accordingly (the variables in capitals after imports)
* configure *rtorrent.rc* with  `method.set_key = event.download.finished,run_autodrop,"execute2={/home/rtorrent/bin/autodrop.py,$d.base_path=}"` (set directory of script accordingly)

### Config File
Default location for config file is *~/.autodrop.conf* but this can be overridden by running autodrop with --config /location/autodrop.conf

# Other notes
This is an early version. It may operate in unexpected ways in some scenarios, and may not handle non-media files correctly.

Please ensure you have enough storage available for the unrar operation.
