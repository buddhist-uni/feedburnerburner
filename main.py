#!/bin/python3
import json
from time import mktime
from pathlib import Path

from utils import FileSyncedSet, system_open, prompt

import feedparser
from yaspin import yaspin
from bs4 import BeautifulSoup

db_dir = Path("~/.feedburnerburner").expanduser()
if not db_dir.exists():
    db_dir.mkdir()
unread_entries = FileSyncedSet(db_dir.joinpath('unread.tsv'), lambda e: e.fbbid)


def guid_to_fbbid(guid: str) -> str:
    return guid.replace(":", "=").replace(",", "_")

class FeedEntry:
    def __init__(self, feed_entry: feedparser.FeedParserDict = None, json_file: Path = None):
        if json_file:
            data = json.loads(json_file.read_text())
            self.title = data.get('title')
            self.summary = data.get('summary')
            self.author = data.get('author')
            self.link = data.get('link')
            self.guid = data.get('guid')
            self.timestamp = data.get('timestamp')
            self.tags = data.get('tags')
            self.status = data.get('status')
        if feed_entry:
            self.title = feed_entry.get('title')
            self.summary = feed_entry.get('summary')
            self.author = feed_entry.get('author')
            self.link = feed_entry.get('link')
            self.guid = feed_entry.get('guid')
            self.timestamp = int(mktime(feed_entry.published_parsed))
            self.tags = [tag.term for tag in feed_entry.get('tags')]
            self.status = "unread"

    @property
    def fbbid(self):
        return guid_to_fbbid(self.guid)

    @property
    def file_path(self):
        return db_dir.joinpath(f"{self.fbbid}.json")

    def save(self):
        self.file_path.write_text(self.json)

    @property
    def json(self) -> str:
        return json.dumps({
            'title': self.title,
            'summary': self.summary,
            'author': self.author,
            'link': self.link,
            'guid': self.guid,
            'timestamp': self.timestamp,
            'tags': self.tags,
            'status': self.status
        }, sort_keys=True)


if __name__ == '__main__':
    unread_items: list[FeedEntry] = []
    with yaspin(text="Loading feed..."):
        for fbbid in unread_entries.items:
            fbbid = fbbid.replace("\n", "")
            if not fbbid:
                continue
            unread_items.append(FeedEntry(json_file=db_dir.joinpath(f"{fbbid}.json")))
        latest_feed = feedparser.parse('https://feeds.feedburner.com/Metafilter')
        for entry in latest_feed.entries:
            feed_entry = FeedEntry(feed_entry=entry)
            if not feed_entry.file_path.exists():
                feed_entry.save()
                unread_entries.add(feed_entry)
                unread_items.append(feed_entry)
    print(f"Found {len(unread_items)} unread items!")
    for entry in unread_items:
        print("Would you like to open this one?")
        print("\tTitle: " + entry.title)
        print("\tSummary: " + entry.summary)
        if prompt("Open this one?"):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            link = soup.find('a')['href']
            system_open(link)
            if prompt("Was this one worth your time?"):
                entry.status = "liked"
                entry.save()
            else:
                entry.status = "disliked"
                entry.save()
        else:
            entry.status = "skipped"
            entry.save()
        unread_entries.remove(entry)
    print("That's all for now, folks!")
