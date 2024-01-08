#!/bin/python3

from collections import defaultdict

from models.base import Corpus
from utils import checklist_prompt

from .base import BaseModel, ModelStatus

class TagCloud:
    def __init__(self):
      self.likes = defaultdict(set)
      self.entries = defaultdict(set)
   
    def add_like(self, tag, entry):
      self.entries[tag].add(entry)
      self.likes[tag].add(entry)
   
    def add_dislike(self, tag, entry):
      self.entries[tag].add(entry)
   
    def top(self, N=30, min_likes=2, min_ratio=0.2):
      ret = list(self.likes.keys())
      ret = [k for k in ret if len(self.likes[k])>=min_likes and (len(self.likes[k])/len(self.entries[k]))>=min_ratio]
      ret.sort(key=lambda k: len(self.likes[k])/len(self.entries[k]), reverse=True)
      self.tops = ret[:N]
      return self.tops

    def posts_with(self, tags):
       ret = set()
       for t in tags:
          ret.update(self.entries[t])
       return ret

class TagModel(BaseModel):
    NAME = "Favorite Tags/Domains"
    DESCRIPTION = "Marks only posts containing favorited tags or link domains as \"important\""
    MIN_DATA = "one tag or domain with two likes"
    def __init__(self, corpus: Corpus = None, **kwargs):
        super().__init__(corpus=corpus, **kwargs)
        self.tags = kwargs.get('tags') or []
        self.domains = kwargs.get('domains') or []
    def analyze(self):
        self.tags_cloud = TagCloud()
        self.domains_cloud = TagCloud()
        for entry in (self.corpus.entries - self.corpus.unseen):
            for tag in entry.tags:
              if entry.status == "liked":
                 self.tags_cloud.add_like(tag, entry)
              else:
                 self.tags_cloud.add_dislike(tag, entry)
            for domain in entry.domains_for_rating():
              if entry.status == "liked":
                self.domains_cloud.add_like(domain, entry)
              else:
                self.domains_cloud.add_dislike(domain, entry)
        ratio = self.corpus.calculate_like_ratio()
        top_tags = self.tags_cloud.top(min_ratio=ratio)
        top_domains = self.domains_cloud.top(min_ratio=ratio)
        if len(top_domains) + len(top_tags) == 0:
           self.status = ModelStatus.Invalid
           print("You haven't liked any tags or domains enought times yet to recommend following any of them, unfortunately.")
           return
        r = len(top_tags)
        print(f"""Top {r} tags are:""")
        for i in range(r):
            tag = top_tags[i]
            print(f"{i+1}. {tag} ({len(self.tags_cloud.likes[tag])}/{len(self.tags_cloud.entries[tag])}={100.0*len(self.tags_cloud.likes[tag])/len(self.tags_cloud.entries[tag]):.1f}%)")
        s = len(top_domains)
        if s > 0:
            print(f"\nYour {s} top-liked domains are:")
            for i in range(s):
                domain = top_domains[i]
                print(f"{i+1}. {domain} ({len(self.domains_cloud.likes[domain])}/{len(self.domains_cloud.entries[domain])}={len(self.domains_cloud.likes[domain])*100.0/len(self.domains_cloud.entries[domain]):.1f}%)")
        self.tags = top_tags
        self.domains = top_domains
        self.status = ModelStatus.Analyzed
        self.calculate_stats()    
    def get_parameters(self):
       ret = super().get_parameters()
       ret['domains'] = self.domains
       ret['tags'] = self.tags
       return ret
    def is_refinable(self):
       return self.status == ModelStatus.Analyzed
    def refine(self):
        print("Select the tags you'd like to subscribe to:")
        selections = [t in self.tags for t in self.tags_cloud.tops]
        selections = checklist_prompt(self.tags_cloud.tops, default=selections)
        self.tags = [self.tags_cloud.tops[i] for i in range(len(selections)) if selections[i]]
        print("Please select domains to subscribe to:")
        selections = [d in self.domains for d in self.domains_cloud.tops]
        selections = checklist_prompt(self.domains_cloud.tops, default=selections)
        self.domains = [self.domains_cloud.tops[i] for i in range(len(selections)) if selections[i]]
        self.calculate_stats()
    def calculate_stats(self):
        toplikes = set()
        for tag in self.tags:
            toplikes.update(self.tags_cloud.likes[tag])
        for domain in self.domains:
            toplikes.update(self.domains_cloud.likes[domain])
        self.precision = float(len(toplikes)) / len(self.tags_cloud.posts_with(self.tags) | self.domains_cloud.posts_with(self.domains))
        self.recall = float(len(toplikes))/len(self.corpus.liked)
        print(f"\nSubscribing to just these would have given you {len(toplikes)}/{int(len(self.corpus.liked))}={100.0*self.recall:.1f}% of the posts you've liked.")
        