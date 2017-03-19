# Numenera
Game file analysis tools for Tides of Numenera written in Python3. For Steam in Windows, these files can be found under
`\Programs\Steam\steamapps\common\Torment Tides of Numenera\WIN\TidesOfNumenera\StreamingAssets\data`

## Requirements
Both scripts need `lxml` to function, `word_count.py` tries to be smart and requires the Natural Language Toolkit (`nltk`) as well.

## Usage
```bash
# Directories are traversed (word_count looks for .stringtable files)
$ python3 word_count.py localized/en/text/conversations
# Individual files are supported as well
$ python3 word_count.py localized/en/text/game/*
# Same for the Tide counter (tide_count looks for .conversation files)
$ python3 tide_count.py conversations
```
