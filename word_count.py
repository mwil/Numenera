#! /usr/bin/env python3

import argparse
import os
import re

from collections import defaultdict

from lxml import etree
import nltk.data


g_stats = defaultdict(int)
g_sentence_set = set()

FILE_EXT = ".stringtable"

BLACK_LIST = (
    r"Script Node \d",
    r"Trigger Conv Node \d",
    r"Follow-up PQ",
    r"Bank \d",
    r"[DEBUG]",
    r"^{.*}$"
)

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

    conv_path = str_path.replace("localized/en/text/", "").replace(FILE_EXT, ".conversation")

    # Count only files that also have a .conversation control file!
    if not os.path.isfile(conv_path):
        return

    l_stats = defaultdict(int)
    sentence_set = set()

    g_stats["file_cnt"] += 1

    str_tree = etree.parse(str_path)
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    for dt in str_tree.findall("//DefaultText"):
        if not dt.text:
            g_stats["node_empty_cnt"] += 1
            continue

        blacklisted = [re.match(pattern, dt.text) for pattern in BLACK_LIST]
        if any(blacklisted):
            g_stats["node_ignored_cnt"] += 1
            continue

        l_stats["node_cnt"] += 1
        l_stats["word_cnt"] += len(dt.text.split())

        # Trying to de-duplicate on a sentence level, collect the split
        # sentences in a set. Sometimes paragraphs are pasted together,
        # on a per-file sentence level the pruning should be good.
        sentences = tokenizer.tokenize(dt.text)
        sentence_set.update(sentences)

    for dt in str_tree.findall("//FemaleText"):
        if dt.text:
            l_stats["fem_node_cnt"] += 1
            l_stats["fem_word_cnt"] += len(dt.text.split())

    for key in ("word_cnt", "node_cnt", "fem_word_cnt", "fem_node_cnt"):
        g_stats[key] += l_stats[key]

    if l_stats["word_cnt"]:
        g_stats["file_non_empty_cnt"] += 1

    for sentence in sentence_set:
        g_stats["words_unique_cnt"] += len(sentence.split())

    g_sentence_set.update(sentence_set)

    if args.verbose and l_stats["word_cnt"] > 5000:
        print("Per file stats of ", str_path)
        print("Word count in file: ", l_stats["word_cnt"])
        print("These words are in these nodes: ", l_stats["node_cnt"])
        print("Female words: {fem_word_cnt} in {fem_node_cnt} nodes".format_map(l_stats))
        print()


################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description=r"Count the in-game words of Tides on Numenera. "\
                        r"These files located at 'TidesOfNumenera_Data\StreamingAssets\data\localized\en\text'")
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

    for (x, y) in ((0, 5), (5, 10), (10, 20), (20, 1000)):
        print("Sentences with {} to {} words: {:,} with {:,} words".format(x, y-1,
            len([sentence for sentence in g_sentence_set if x<len(sentence.split())<=y]),
            len([word for sentence in g_sentence_set for word in sentence.split() if x<len(sentence.split())<=y])))

