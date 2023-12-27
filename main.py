#!/bin/python3
import json
from time import mktime
from urllib.parse import urlparse
from pathlib import Path
from functools import cache
import yaml

from utils import (
    FileSyncedSet,
    system_open,
    prompt,
    radio_dial
)

import feedparser
from yaspin import yaspin
from bs4 import BeautifulSoup

db_dir = Path("~/.feedburnerburner").expanduser()
if not db_dir.exists():
    db_dir.mkdir()
unread_entries = FileSyncedSet(db_dir.joinpath('unread.tsv'), lambda e: e.fbbid)
SETTINGS_FILE = db_dir.joinpath('settings.yaml')

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
            self.clicked_links = data.get('clicked_links') or []
        if feed_entry:
            self.title = feed_entry.get('title')
            self.summary = feed_entry.get('summary')
            self.author = feed_entry.get('author')
            self.link = feed_entry.get('link')
            self.guid = feed_entry.get('guid')
            self.timestamp = int(mktime(feed_entry.published_parsed))
            self.tags = [tag.term for tag in feed_entry.get('tags')]
            self.status = "unread"
            self.clicked_links = []

    @property
    def fbbid(self):
        return guid_to_fbbid(self.guid)

    @property
    @cache
    def soup(self):
        return BeautifulSoup(self.summary, 'html.parser')

    @property
    @cache
    def links(self):
        return [a['href'] for a in self.soup.find_all('a', href=True)]
    
    def links_for_rating(self):
        if self.status == "liked":
            return self.clicked_links or self.links
        else:
            return self.links
    
    def domains_for_rating(self):
        links = self.links_for_rating()
        return list({'.'.join(urlparse(url).hostname.split('.')[-2:]) for url in links})

    @property
    def file_path(self):
        return db_dir.joinpath(f"{self.fbbid}.json")

    def save(self):
        self.file_path.write_text(self.json())

    def json(self) -> str:
        return json.dumps({
            'title': self.title,
            'summary': self.summary,
            'author': self.author,
            'link': self.link,
            'guid': self.guid,
            'timestamp': self.timestamp,
            'tags': self.tags,
            'status': self.status,
            'clicked_links': self.clicked_links,
        }, sort_keys=True)


def display_loop(unread_items: list[FeedEntry]):
    for entry in unread_items:
        print("Would you like to open this one?")
        print("\tTitle: " + entry.title)
        print("\tSummary: " + entry.summary)
        links = entry.links
        choice = radio_dial([
            "Not interested",
            "Show again later",
        ]+links)
        if choice == 0:
            entry.status = "skipped"
            entry.save()
            unread_entries.remove(entry)
            continue
        if choice == 1:
            continue
        while choice > 1:
            print("  How was it?")
            link = links.pop(choice-2)
            entry.clicked_links.append(link)
            system_open(link)
            choice = radio_dial([
                "Waste of time",
                "Worthwhile",
            ]+links)
        if choice == 0:
            entry.status = "disliked"
            entry.save()
            unread_entries.remove(entry)
            continue
        if choice == 1:
            entry.status = "liked"
            entry.save()
            unread_entries.remove(entry)
            continue

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
    if len(unread_items) > 0 and SETTINGS_FILE.exists():
        settings = yaml.safe_load(SETTINGS_FILE.read_text())
        if settings['algo'] == "tagsubscriber":
            domains = set(settings['domains'])
            tags = set(settings['tags'])
            highpri = [item for item in unread_items if any(d in domains for d in item.domains_for_rating()) or any(t in tags for t in item.tags)]
            if len(highpri) == 0:
                print("But none of them are important")
            else:
                print(f"{len(highpri)} of them are marked priority based on the tags and domains you're subscribed to:")
                display_loop(highpri)
                unread_items = [item for item in unread_items if item not in highpri]
            if len(unread_items) > 0:
                if not prompt("Continue to read the unimportant posts?"):
                    print("Sounds good! Enjoy your day! :)")
                    quit()
    display_loop(unread_items)
    print("That's all for now, folks!")
