#!/bin/python3

from functools import cache
import feedparser
from pathlib import Path
import json
from time import mktime
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def guid_to_fbbid(guid: str) -> str:
    return guid.replace(":", "=").replace(",", "_")


class FeedEntry:
    def __init__(self, feed_entry: feedparser.FeedParserDict = None,
                 json_file: Path = None, db_dir: Path = None):
        if json_file:
            self.file_path = json_file
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
            if not db_dir:
                raise RuntimeError(
                    "FeedEntry needs either a json_file or db_dir Path")
            self.title = feed_entry.get('title')
            self.summary = feed_entry.get('summary')
            self.author = feed_entry.get('author')
            self.link = feed_entry.get('link')
            self.guid = feed_entry.get('guid')
            self.file_path = db_dir.joinpath(f"{self.fbbid}.json")
            self.timestamp = int(mktime(feed_entry.published_parsed))
            self.tags = [tag.term for tag in feed_entry.get('tags')]
            self.status = "unread"
            self.clicked_links = []

    # Sort posts in Chronological Order by default
    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __gt__(self, other):
        return self.timestamp > other.timestamp

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
        return list(
            {'.'.join(urlparse(url).hostname.split('.')[-2:]) for url in links})

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
