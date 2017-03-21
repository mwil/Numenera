#! /usr/bin/env python3

import argparse
import os
import re
import string

from collections import defaultdict

from lxml import etree
from nltk.tokenize import word_tokenize, sent_tokenize


g_stats = defaultdict(int)
g_sentence_set = set()

FILE_EXT = ".stringtable"

# Certain nodes do not represent in-game text, skip the most common ones
BLACK_LIST = (
    r"^Script Node \d",
    r"^Trigger Conv Node \d",
    r"^Follow-up PQ",
    r"^Bank \d",
    r"^[DEBUG]",
    r"^{.*}$"
)

MAN_GENERIC_SET = set((
    "lad", "laddie", "sir", "lord", "fellow", "fella",
    "hero", "he", "he's", "he'd", "he'll", "him", "himself",
    "his", "brother", "brother's", "man", "boy", "male")
)
FEM_GENERIC_SET = set((
    "lass", "lassie", "ma'am", "madam", "madame", "lady",
    "miss", "maid", "heroine", "she", "she's", "she'd", "she'll",
    "her", "herself", "sister", "sister's", "woman", "girl", "female")
)
ALL_GENERIC_SET = MAN_GENERIC_SET | FEM_GENERIC_SET

RESULT_STR = """\
Number of files: {file_cnt}, non-empty: {file_non_empty_cnt}
Word count in all files: {word_cnt:,}
These words are in {node_cnt:,} nodes, with {node_empty_cnt:,} nodes being empty, {node_ignored_cnt:,} ignored.
Female words: {fem_word_cnt:,} in {fem_node_cnt:,} nodes
---------------------------------------------------------------------
Words from per-file unique sentences: {words_unique_cnt:,}"""


################################################################################
def traverse(rootdir):
    for dirpath, _, filenames in os.walk(rootdir):
        for filename in filenames:
            if filename.endswith(FILE_EXT):
                count_file(os.path.join(dirpath, filename))


################################################################################
def count_file(str_path):
    global args, g_stats, g_sentence_set

    conv_path  = str_path.replace("localized/en/text/", "").replace(FILE_EXT, ".conversation")
    quest_path = str_path.replace("localized/en/text/", "").replace(FILE_EXT, ".quest")

    # Count only files that also have a .conversation/.quest control file!
    if not (os.path.isfile(conv_path) or os.path.isfile(quest_path)):
        return

    l_stats = defaultdict(int)
    l_sentence_set = set()

    g_stats["file_cnt"] += 1

    str_tree = etree.parse(str_path)

    for dt in str_tree.findall("//DefaultText"):
        if not dt.text:
            g_stats["node_empty_cnt"] += 1
            continue

        blacklisted = [re.search(pattern, dt.text) for pattern in BLACK_LIST]
        if any(blacklisted):
            g_stats["node_ignored_cnt"] += 1
            continue

        l_stats["node_cnt"] += 1
        l_stats["word_cnt"] += len(dt.text.split())

        # Trying to de-duplicate on a sentence level, collect the split
        # sentences in a set. Sometimes paragraphs are pasted together,
        # on a per-file sentence level the pruning should be good.
        # added: global sentence set!
        l_sentence_set.update(sent_tokenize(dt.text))

        for ft in dt.findall("../FemaleText"):
            if ft.text:
                l_stats["fem_node_cnt"] += 1
                l_stats["fem_word_cnt"] += len(ft.text.split())

                man_word_set = {mw.lower().strip(string.punctuation) for mw in dt.text.split()}
                fem_word_set = {fw.lower().strip(string.punctuation) for fw in ft.text.split()}

                gender_diff_set = (man_word_set ^ fem_word_set) - ALL_GENERIC_SET

                if args.verbose and len(gender_diff_set) > 5:
                    print("Conversation in file ", str_path)
                    print("Male:   ", dt.text)
                    print("Female: ", ft.text)
                    print("-"*80)
                    print()

    for key in ("word_cnt", "node_cnt", "fem_word_cnt", "fem_node_cnt"):
        g_stats[key] += l_stats[key]

    if l_stats["word_cnt"]:
        g_stats["file_non_empty_cnt"] += 1

    for sentence in l_sentence_set:
        g_stats["words_unique_cnt"] += len(sentence.split())

    g_sentence_set.update(l_sentence_set)

    if args.verbose and l_stats["word_cnt"] > 10000:
        print("Per file stats of ", str_path)
        print("Word count in file: ", l_stats["word_cnt"])
        print("These words are in these nodes: ", l_stats["node_cnt"])
        print("Female words: {fem_word_cnt} in {fem_node_cnt} nodes".format_map(l_stats))


################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="Count the in-game words of Tides on Numenera. "\
                        "These files located at 'TidesOfNumenera_Data/StreamingAssets/data/localized/en/text'")
    parser.add_argument("path", nargs="+",
            help="Top-level directories with {} files inside, or individual files.".format(FILE_EXT))
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    for path in args.path:
        if os.path.isfile(path):
            if path.endswith(FILE_EXT):
                count_file(path)
            else:
                print("Ignoring file {}, unexpected file type!".format(path))
        else:
            traverse(path)

    print("-"*30, "Results", "-"*30)
    print(RESULT_STR.format_map(g_stats))
    print("-"*80)
    print("{:,} words in {:,} globally unique sentences.".format(
            sum([len(sentence.split()) for sentence in g_sentence_set]), len(g_sentence_set)))

