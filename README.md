# iplodcast
Trawls through your get-iplayer history and generates podcast feeds.

_Note: very early development version, but totally functional._

It's configured using a yaml file in the current directory (or specified on the command line using `--config`).

This requires the following modules:

* mutagen
* pytz
* pyaml
* rfeed (but not the one in PyPi)

To build, use `python3 -m build` (using _python-build_), then install the resulting tar.gz file that is generated (by default in `dist`) using `pip` or `pipx`.

Limitations:

* Must run on same machine as `get-iplayer`.
* Everything happens in a single local filesystem,
  because it hard links the files into the webserver rather than copying them.
