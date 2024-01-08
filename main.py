#!/bin/python3
from pathlib import Path
import yaml

from utils import (
    system_open,
    prompt,
    radio_dial
)
from models.feed import FeedEntry
from settings import (
    settings,
    SETTINGS_FILE,
    unread_entries,
    db_dir,
)

import feedparser
from yaspin import yaspin

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
            feed_entry = FeedEntry(feed_entry=entry, db_dir=db_dir)
            if not feed_entry.file_path.exists():
                feed_entry.save()
                unread_entries.add(feed_entry)
                unread_items.append(feed_entry)
    print(f"Found {len(unread_items)} unread items!")
    if len(unread_items) > 0 and SETTINGS_FILE.exists():
        if settings['algo'] == "tagsubscriber" or settings['algo'] == 'Favorite Tags/Domains':
            domains = set(settings.get('domains'))
            tags = set(settings.get('tags'))
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
