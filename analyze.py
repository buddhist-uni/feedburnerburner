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

class TagCloud:
   def __init__(self):
      self.likes = defaultdict(list)
      self.counts = defaultdict(float)
   
   def add_like(self, tag, entry):
      self.counts[tag] += 1.0
      self.likes[tag].append(entry)
   
   def add_dislike(self, tag):
      self.counts[tag] += 1.0
   
   def top(self, N=30, min_likes=2, min_ratio=0.2):
      ret = list(self.likes.keys())
      ret = [k for k in ret if len(self.likes[k])>=min_likes and (len(self.likes[k])/self.counts[k])>=min_ratio]
      ret.sort(key=lambda k: len(self.likes[k])/self.counts[k], reverse=True)
      return ret[:N]

entries = []
tags = TagCloud()
domains = TagCloud()
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
            if entry.status == 'liked':
               tags.add_like(tag, entry)
            else:
               tags.add_dislike(tag)
        for domain in entry.domains_for_rating():
           if entry.status == 'liked':
              domains.add_like(domain, entry)
           else:
              domains.add_dislike(domain)
ratio = liked/count
print(f"So far you've liked {int(liked)}/{int(count)}={ratio*100.0:.1f}% of the posts.")
top_tags = tags.top(min_ratio=ratio)
r = len(top_tags)
if r > 0:
  print(f"""Top {r} tags are:""")
  toplikes = set()
  for i in range(r):
    tag = top_tags[i]
    toplikes.update(tags.likes[tag])
    print(f"{i+1}. {tag} ({len(tags.likes[tag])}/{int(tags.counts[tag])}={100.0*len(tags.likes[tag])/tags.counts[tag]:.1f}%)")
  top_domains = domains.top(min_ratio=ratio)
  s = len(top_domains)
  if s > 0:
     print(f"\nYour {s} top-liked domains are:")
     for i in range(s):
        domain = top_domains[i]
        toplikes.update(domains.likes[domain])
        print(f"{i+1}. {domain} ({len(domains.likes[domain])}/{int(domains.counts[domain])}={len(domains.likes[domain])*100.0/domains.counts[domain]:.1f}%)")
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
       toplikes.update(tags.likes[tag])
    for domain in domains:
       toplikes.update(domains.likes[domain])
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

