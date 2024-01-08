#!/bin/python3
from collections import defaultdict
import yaml
from utils import (
   prompt,
   checklist_prompt,
)
from main import (
    SETTINGS_FILE,
    yaspin,
    db_dir,
)
from models import FeedEntry

entries = []
tags = []
tag_likes = defaultdict(list)
tag_count = defaultdict(float)
domains = []
domain_counts = defaultdict(float)
domain_likes = defaultdict(list)
count = 0.0
liked = 0.0
with yaspin(text='Crunching the numbers...'):
    for fd in db_dir.iterdir():
        if fd.name.endswith('.json'):
            entries.append(FeedEntry(json_file=fd))
    for entry in entries:
        count += 1.0
        inc = 0.0
        if entry.status == 'liked':
            liked += 1.0
        for tag in entry.tags:
            tag_count[tag] += 1.0
            if entry.status == 'liked':
                tag_likes[tag].append(entry)
        for domain in entry.domains_for_rating():
           domain_counts[domain] += 1.0
           if entry.status == 'liked':
              domain_likes[domain].append(entry)
    tags = list(tag_count.keys())
    domains = list(domain_likes.keys())
    tags.sort(key=lambda k: len(tag_likes[k])/tag_count[k], reverse=True)
    domains.sort(key=lambda k: len(domain_likes[k])/domain_counts[k], reverse=True)
    tags = [k for k in tags if len(tag_likes[k])>1 and tag_count[k]>1 and len(tag_likes[k])/tag_count[k]>liked/count]
    domains = [k for k in domains if len(domain_likes[k])>1 and len(domain_likes[k])/domain_counts[k]>liked/count]
r = min(30, len(tags))
print(f"So far you've liked {int(liked)}/{int(count)}={liked*100.0/count:.1f}% of the posts.")
if r > 0:
  print(f"""Top {r} tags are:""")
  toplikes = set()
  for i in range(r):
    tag = tags[i]
    toplikes.update(tag_likes[tag])
    print(f"{i+1}. {tag} ({len(tag_likes[tag])}/{int(tag_count[tag])}={100.0*len(tag_likes[tag])/tag_count[tag]:.1f}%)")
  s = min(30, len(domains))
  if s > 0:
     print(f"\nYour {s} top-liked domains are:")
     for i in range(s):
        domain = domains[i]
        toplikes.update(domain_likes[domain])
        print(f"{i+1}. {domain} ({len(domain_likes[domain])}/{int(domain_counts[domain])}={len(domain_likes[domain])*100.0/domain_counts[domain]:.1f}%)")
  print(f"\nSubscribing to just these would have given you {len(toplikes)}/{int(liked)}={len(toplikes)*100.0/liked:.1f}% of the posts you've liked.")
  if prompt("Would you like to filter your posts based on the above? (n=See all, ctrl+c to Cancel)"):
    print("Select the tags you'd like to subscribe to:")
    selections = checklist_prompt(tags[:r], default=True)
    tags = [tags[i] for i in range(r) if selections[i]]
    print("Please select domains to subscribe to:")
    selections = checklist_prompt(domains[:s], default=True)
    domains = [domains[i] for i in range(s) if selections[i]]
    toplikes = set()
    for tag in tags:
       toplikes.update(tag_likes[tag])
    for domain in domains:
       toplikes.update(domain_likes[domain])
    print(f"\nSubscribing to just these would have given you {len(toplikes)}/{int(liked)}={len(toplikes)*100.0/liked:.1f}% of the posts you've liked.")
    SETTINGS_FILE.write_text(yaml.dump({
       "algo": "tagsubscriber",
       "domains": domains,
       "tags": tags,
    }))
  else:
    SETTINGS_FILE.write_text(yaml.dump({"algo": "none"}))
  print("Settings successfully saved!")
else:
  print("Insufficient data to recommend even a single tag.")

