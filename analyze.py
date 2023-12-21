#!/bin/python3
from collections import defaultdict
from main import (
    yaspin,
    db_dir,
    FeedEntry
)

entries = []
tags = []
tag_likes = defaultdict(list)
count = 0.0
liked = 0.0
with yaspin(text='Crunching the numbers...'):
    for fd in db_dir.iterdir():
        if fd.name.endswith('.json'):
            entries.append(FeedEntry(json_file=fd))
    tag_count = defaultdict(float)
    for entry in entries:
        count += 1.0
        inc = 0.0
        if entry.status == 'liked':
            liked += 1.0
        for tag in entry.tags:
            tag_count[tag] += 1.0
            if entry.status == 'liked':
                tag_likes[tag].append(entry)
    tags = list(tag_count.keys())
    tags.sort(key=lambda k: len(tag_likes[k])/tag_count[k], reverse=True)
    tags = [k for k in tags if len(tag_likes[k])>1 and tag_count[k]>1 and len(tag_likes[k])/tag_count[k]>liked/count]
r = min(30, len(tags))
print(f"So far you've liked {int(liked)}/{int(count)}={liked*100.0/count:.1f}% of the posts.")
if r > 0:
  print(f"""Top {r} tags are:""")
  toplikes = set()
  for i in range(r):
    tag = tags[i]
    toplikes.update(tag_likes[tag])
    print(f"{i+1}. {tag} ({len(tag_likes[tag])}/{int(tag_count[tag])}={100.0*len(tag_likes[tag])/tag_count[tag]:.1f}%)")
  print(f"\nSubscribing to just these would have given you {len(toplikes)}/{int(liked)}={len(toplikes)*100.0/liked:.1f}% of the posts you've liked.")
else:
  print("Insufficient data to recommend even a single tag.")

