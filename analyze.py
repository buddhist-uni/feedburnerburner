#!/bin/python3
from collections import defaultdict
from main import (
    yaspin,
    db_dir,
    FeedEntry
)

entries = []
tags = []
count = 0.0
liked = 0.0
with yaspin(text='Crunching the numbers...'):
    for fd in db_dir.iterdir():
        if fd.name.endswith('.json'):
            entries.append(FeedEntry(json_file=fd))
    tag_count = defaultdict(float)
    tag_likes = defaultdict(float)
    for entry in entries:
        count += 1.0
        inc = 0.0
        if entry.status == 'liked':
            liked += 1.0
            inc = 1.0
        for tag in entry.tags:
            tag_count[tag] += 1.0
            tag_likes[tag] += inc
    tags = list(tag_count.keys())
    tags.sort(key=lambda k: tag_likes[k]/tag_count[k], reverse=True)
    tags = [k for k in tags if tag_likes[k]>1 and tag_count[k]>1 and tag_likes[k]/tag_count[k]>liked/count]
r = min(30, len(tags))
print(f"So far you've liked {int(liked)}/{int(count)}={liked*100.0/count:.1f}% of the posts.")
if r > 0:
  print(f"""Top {r} tags are:""")
  for i in range(r):
    tag = tags[i]
    print(f"{i+1}. {tag} ({int(tag_likes[tag])}/{int(tag_count[tag])}={100.0*tag_likes[tag]/tag_count[tag]:.1f}%)")
else:
  print("Insufficient data to recommend even a single tag.")

