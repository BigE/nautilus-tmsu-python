# nautilus-tmsu-python
This is a Nautilus Extension written in Python for GTK 4

## Requirements
* python (>=3.10)
* nautilus-python (>=4.0)

## Install
Installation is simple using `make install` to copy or `make dev_install` to
make symlinks for development purposes. The `Makefile` automatically restarts
Nautilus as part of each install process. You can also call the
`restart_nautilus` target using `make restart_nautilus` to trigger a manual
restart, or just type `nautilus -q` into your terminal.
