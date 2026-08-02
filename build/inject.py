# -*- coding: utf-8 -*-
# Substitutes the four generated data files into the template.
# Writes glossary_wordle.html next to this script, and ../index.html when run from a repo
# checkout (that is the file GitHub Pages serves).
import os
base = os.path.dirname(os.path.abspath(__file__)) + os.sep

tpl = open(base + "game_template.html", encoding="utf-8").read()
out = (tpl
       .replace("__EN_WORDS__", open(base + "en_words.txt", encoding="utf-8").read())
       .replace("__AR_WORDS__", open(base + "ar_words.txt", encoding="utf-8").read())
       .replace("__EN_DICT__", open(base + "en_dict.txt", encoding="utf-8").read())
       .replace("__AR_DICT__", open(base + "ar_dict.txt", encoding="utf-8").read()))

open(base + "glossary_wordle.html", "w", encoding="utf-8").write(out)
targets = ["glossary_wordle.html"]

parent_index = os.path.normpath(os.path.join(base, os.pardir, "index.html"))
if os.path.exists(parent_index):          # repo checkout: refresh the published page too
    open(parent_index, "w", encoding="utf-8").write(out)
    targets.append("../index.html")

print("built %s, size: %d" % (" + ".join(targets), len(out)))
