#!/bin/python3

from pathlib import Path
import yaml

from utils import (
    FileSyncedSet,
)

db_dir = Path("~/.feedburnerburner").expanduser()
if not db_dir.exists():
    db_dir.mkdir()
unread_entries = FileSyncedSet(
    db_dir.joinpath('unread.tsv'),
    lambda e: e.fbbid)
SETTINGS_FILE = db_dir.joinpath('settings.yaml')

settings = {}
if SETTINGS_FILE.exists():
    settings = yaml.safe_load(SETTINGS_FILE.read_text())
