#!/usr/bin/env python

# You will need to install the following modules: rfeed, pytz, pyaml, mutagen

# Note do not use the version of rfeed in pypi. It's old. Instead:
# env/bin/pip install \
#   https://github.com/svpino/rfeed/archive/refs/heads/master.zip

import argparse
import csv
import datetime
import mutagen
import os
import pathlib
import re
import rfeed
import yaml
from pytz import timezone, utc

DEFAULT_CONFIG = "iplodcast.yaml"
london = timezone("Europe/London")
RE_CLEANUP = re.compile(r"[ :/]+")


def clean_name(str):
    return RE_CLEANUP.sub("_", str)


def padnum(str):
    return f"00000000{str or ''}"[-8:]


def get_episodes(programmes, history_file):

    searches = []
    episodes = {}
    for p in programmes:
        name = p.get("name")
        match = p.get("match")
        episodes[name] = []
        max_age = datetime.timedelta(days=int(p.get("maxage", "365")))
        if match:
            searches.append((name, re.compile(match), max_age))
        else:
            searches.append((name, name, max_age))

    with open(history_file, newline="") as f:
        history = csv.DictReader(
            f,
            fieldnames=(
                "pid",
                "name",
                "episode",
                "type",
                "timeadded",
                "mode",
                "filename",
                "versions",
                "duration",
                "desc",
                "channel",
                "categories",
                "thumbnail",
                "guidance",
                "web",
                "episodenum",
                "seriesnum",
                "tail",
            ),
            delimiter="|",
        )
        for ep in history:
            date = datetime.datetime.utcfromtimestamp(
                int(ep.get("timeadded") or "0")
            )
            for name, search, max_age in searches:
                if datetime.datetime.now() - date < max_age:
                    if type(search) == str:
                        if ep.get("name") == name:
                            episodes[name].append(ep)
                    elif search.match(ep.get("name")):
                        episodes[name].append(ep)

    return episodes


def make_programme_feed(prog, all_episodes, output_dir, url_base):
    podcast_name = prog.get("name")
    podcast_description = prog.get("description", "")

    author = "BBC"
    image = None

    episodes = all_episodes[podcast_name]

    if len(episodes) == 0:
        print(f"No episodes of {podcast_name}")
        return

    output_path = pathlib.Path(output_dir)
    clean_path = clean_name(podcast_name)
    copy_path = output_path / clean_path
    output_rss = f"{clean_path}.rss"

    copy_path.mkdir(exist_ok=True)

    items = []
    for ep in episodes:
        filename = pathlib.Path(ep.get("filename"))
        if not filename.is_file():
            continue
        info = mutagen.File(filename)

        summary = "".join(info.get("\xa9lyr"))
        title = ep.get("episode")
        subtitle = ep.get("desc")
        author = ep.get("channel")
        image = ep.get("thumbnail")
        duration = ep.get("duration")
        guid = ep.get("web")
        episode = ep.get("episodenum")
        season = ep.get("seriesnum")
        sequence = f"{padnum(season)}:{padnum(episode)}"

        suffix = filename.suffix
        mimetype = None
        if suffix == ".mp3":
            mimetype = "audio/mpeg"
        elif suffix == ".m4a":
            mimetype = "audio/mp4"
        elif suffix == ".aac":
            mimetype = "audio/aac"
        elif suffix == ".ogg":
            mimetype = "audio/ogg"
        elif suffix == ".opus":
            mimetype = "audio/opus"
        elif suffix == ".flac":
            mimetype = "audio/flac"

        newfile = f"{clean_path}/{filename.name}"
        url = f"{url_base}/{newfile}"
        hardlink = copy_path / filename.name
        hardlink.unlink(missing_ok=True)
        hardlink.hardlink_to(filename)

        itunes_item = rfeed.iTunesItem(
            duration=duration,
            image=image,
            subtitle=subtitle,
            summary=summary,
            title=title,
            episode=episode,
            season=season,
            author=author,
            order=f"{season}:{episode}",
        )

        item = rfeed.Item(
            title=title,
            description=summary,
            guid=rfeed.Guid(guid, isPermaLink=False),
            pubDate=datetime.datetime.utcfromtimestamp(
                int(ep.get("timeadded"))
            ),
            enclosure=rfeed.Enclosure(
                url=url,
                length=filename.stat().st_size,
                type=mimetype,
            ),
            extensions=[itunes_item],
        )

        items.append(item)

    itunes = rfeed.iTunes(
        author=author,
        image=image,
    )

    feed = rfeed.Feed(
        title=podcast_name,
        description=podcast_description,
        language="en",
        link=f"{url_base}/{output_rss}",
        lastBuildDate=utc.normalize(london.localize(datetime.datetime.now())),
        items=items,
        extensions=[itunes],
    )

    with open(output_path / output_rss, "w") as fp:
        print(feed.rss(), file=fp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=pathlib.Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    with args.config.open("r") as c:
        config = yaml.safe_load(c)

    output_dir = config["output_dir"]
    url_base = config["url_base"]
    programmes = config["programmes"]
    history_file = config.get(
        "history_file",
        f"{os.environ['HOME']}/.get_iplayer/download_history"
    )

    all_episodes = get_episodes(programmes, history_file)

    for programme in programmes:
        make_programme_feed(programme, all_episodes, output_dir, url_base)


if __name__ == "__main__":
    main()
