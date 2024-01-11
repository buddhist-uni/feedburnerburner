# FeedBurner Burner

A command-line utility for quickly reading MetaFilter Posts.

## Installation

`pip install -r requirements.txt`

Note that the project requires python3 and has only been tested on Android and Linux.

## Reading

`python main.py`

Run this script to load the metafilter RSS and read through the posts in chronological order.

The script will record which posts you liked and which you didn't to ~/.feedburnerburner.

## Customizing your feed

`python analyze.py`

After you've been reading for a while, you can run this script to create a custom posts filter which will only show you those posts you're likely to rate as worthwhile.
