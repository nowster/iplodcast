# iplodcast
Trawls through your get-iplayer history and generates podcast feeds.

_Note: very early development version, but totally functional._

It's configured using a yaml file in the current directory (or specified on the command line using `--config`).

This requires the following modules:

* mutagen
* pytz
* pyaml
* rfeed

All but rfeed can be installed from PyPy. The copy there is out of date but has a higher version number. Install the correct version using:

```
env/bin/pip install https://github.com/svpino/rfeed/archive/refs/heads/master.zip
```

Limitations:

* Must run on same machine as `get-iplayer`.
* Everything happens in a single local filesystem,
  because it hard links the files into the webserver rather than copying them.
