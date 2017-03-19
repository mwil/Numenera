# Numenera
Game file analysis tools for Tides of Numenera written in Python3.

## Requirements
Both scripts need `lxml` to function, `word_count.py` tries to be smart and requires the Natural Language Toolkit (`nltk`) as well.

## Usage
```bash
# Directories are traversed
$ python3 word_count.py localized/en/text/conversations
# Individual files are supported as well
$ python3 word_count.py localized/en/text/game/*
# Same for the Tide counter
$ python3 tide_count.py conversations
```
