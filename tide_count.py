#! /usr/bin/env python3

import argparse
import os
import pprint

from collections import defaultdict
from lxml import etree

g_col_stats = defaultdict(int)
g_col_weighted = defaultdict(int)
g_col_multi = defaultdict(int)

FILE_EXT = ".conversation"
TIDE_WEIGHTS = {"Tiny": 1, "Small":2, "Moderate":3, "Huge":5}

xpath_find_raiseTide_Data    = etree.XPath("ScriptCall/Data/FullName[starts-with(text(), 'Void RaisePlayerTide')]/..")
xpath_text_scriptCall_Params = etree.XPath("Parameters/string/text()")
xpath_text_DefTxt_by_nodeid  = etree.XPath("//ID[text()=$nodeid]/../DefaultText/text()")

################################################################################
def traverse(rootdir):
    for dirpath, _, filenames in os.walk(rootdir):
        for filename in filenames:
            if filename.endswith(FILE_EXT):
                count_file(os.path.join(dirpath, filename))


################################################################################
def count_file(filepath):
    global args, g_col_stats, g_col_weighted, g_col_multi

    stringpath = filepath.replace("conversations", "localized/en/text/conversations")
    stringpath = stringpath.replace(".conversation", ".stringtable")

    if not os.path.isfile(stringpath):
        return

    conv_tree = etree.parse(filepath)
    str_tree  = etree.parse(stringpath)

    # All communication nodes have an <OnEnterScripts> element that is executed when the option was chosen.
    # We search for all <ScriptCall> elements that call RaisePlayerTide(), and check their contents.
    for enter_script in conv_tree.findall("//OnEnterScripts"):
        tide_changes = []
        raise_calls = xpath_find_raiseTide_Data(enter_script)

        # `raise_calls` can also be empty when the script calls other functions,
        # this just skips them automatically, otherwise collect all tide changes
        for call in raise_calls:
            color, amount = xpath_text_scriptCall_Params(call)

            tide_changes.append((color, amount))

            g_col_stats[color] += 1
            g_col_weighted[color] += TIDE_WEIGHTS[amount]

            if args.verbose and color in ("Indigo") and amount in ("Moderate", "Huge"):
                print("{}: {} -> {}".format(filepath, color, amount))

                # Find the corresponding in-game string in the localized files
                nodeid = enter_script.findtext("../NodeID")
                print("{[0]} [nodeid={}]\n".format(xpath_DefTxt_by_nodeid(str_tree, nodeid=nodeid), nodeid))

        if len(raise_calls) > 1:
            # Several tides are manipulated in a single node
            g_col_multi[frozenset([col for col, _ in tide_changes])] += 1

            if False and args.verbose\
                and "Blue"   in [col for col, _ in tide_changes]\
                and "Silver" in [col for col, _ in tide_changes]:

                print("{}: {}".format(filepath, tide_changes))

                # Find the corresponding in-game string in the localized files
                nodeid = enter_script.findtext("../NodeID")
                print("{[0]} [nodeid={}]\n".format(xpath_DefTxt_by_nodeid(str_tree, nodeid=nodeid), nodeid))


################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="Count the Tide changes in Tides on Numenera. "\
                        "These files located at 'TidesOfNumenera_Data/StreamingAssets/data/conversations'")
    parser.add_argument("path", nargs="+",
            help="Top-level directories with '{}' files inside, or individual files.".format(FILE_EXT))
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

    print("Color appearances: ")
    for color, count in g_col_stats.items():
        print("Color: {}, count: {}, weighted count: {}".format(color, count, g_col_weighted[color]))
    print("Multi changes at once:", sum(v for v in g_col_multi.values()))
    print()
    pprint.pprint(g_col_multi)

