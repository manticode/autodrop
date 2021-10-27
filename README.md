# Autodrop
MIT License

### Requires:
* CentOS or Debian or suitable Linux operating sytem
* **Python 3.8+** (may work on older Python 3 versions, but this project was created with Python 3.8)
* **rtorrent** installed and configured
* **unrar** and **rsync** installed
* static IP address or dynamic DNS

### Usage
* Configure the global variables accordingly (the variables in capitals after imports)
* configure *rtorrent.rc* with  `**method.set_key = event.download.finished,run_autodrop,"execute2={/home/rtorrent/bin/autodrop.py,$d.directory=}"** (set directory of script accordingly)`

# Other notes
This is an early version that works as intended. It may operate in unexpected ways in some scenarios, and may not handle non-media files correctly.

Please ensure you have enough storage available for the unrar operation.
