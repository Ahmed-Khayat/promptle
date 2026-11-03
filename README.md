# Glossle · خمِّن

A bilingual, Wordle-style daily word game (formerly Promptle) built on the **ICAIRE AI Glossary**. Guess the hidden
AI term; each guess must be a real word of the shown length; coloured tiles give feedback. When
you solve it, you get the term's definition and its equivalent in the other language — the point
is that you learn something.

**Play:** https://ahmed-khayat.github.io/promptle/

| | English | العربية |
|---|---|---|
| Answer pool | 45 well-known AI terms, 5–7 letters | 44 terms, 4–6 letters (RTL) |
| Accepted guesses | 87,632 words | 87,770 words |

## How it plays

- **Three puzzles a day: Easy, Medium and Hard.** Each tier has its own word pool and its own
  date-derived word, so everyone on the same tier sees the same one. Solve or fail and that tier
  locks until local midnight. The tier is switched from the pill in the header.
- **Any real word is a valid guess**, not just AI terms — that's what makes it feel like Wordle.
  The glossary term is only ever the hidden answer.
- **Hints show on the board.** A hint draws the letter, in green, in its correct position on the
  row you are typing. It never reveals a letter you already have green. Easy starts with two
  letters shown and adds one after every miss; Medium has 3 hints; Hard has 1.
- **Easy and Medium have no fail state** — running out of rows simply shows the word. Hard keeps
  the real "Out of tries".
- **Stats are one record per language**, shared by the tiers: the first tier finished each day
  counts, and a later win on another tier upgrades a same-day loss.
- **Practice mode** frees the daily lock: add `?practice=1` to the URL, or press
  *Play more words* on the result card. It never touches your saved stats or the daily word.
- **Passport**: every term you reach the end of (solved or shown) is kept, with its definition and
  tier, under the menu.
- Arabic is forgiving about spelling — أ/ا, ة/ه and ى/ي are treated as the same letter — and uses
  the standard **Arabic 101** PC keyboard layout.

## Repository layout

```
index.html          the game — one self-contained file, no build step to serve it
build/              the pipeline that generates it
  game_template.html    HTML/CSS/JS with __EN_WORDS__ / __AR_WORDS__ / __EN_DICT__ / __AR_DICT__
  build_all.py          reads the glossary + word lists, writes the four data files
  inject.py             substitutes those into the template -> index.html
  en_words.txt          answer bank: { definition, translation } per term
  ar_words.txt
  en_dict.txt           accepted-guess dictionaries
  ar_dict.txt
  words_alpha.txt       source English word list (~370k)
docs/ARCHITECTURE.md   how the daily lock, scoring and filters actually work
```

## Rebuilding

```bash
cd build
python3 build_all.py     # regenerates the four data files
python3 inject.py        # writes ../index.html
```

`build_all.py` reads the glossary from the
[AI-Glossary-Challenge-by-ICAIRE](https://github.com/) repo (`data/glossary.json`, 1,242 entries)
and an Arabic frequency list. Both paths are constants at the top of the file.

**Two source files are not committed:**

| File | Why | How to get it |
|---|---|---|
| `ar_full_raw.txt` (41 MB) | too large for git | [hermitdave/FrequencyWords](https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ar/ar_full.txt) |
| `glossary.json` | belongs to the glossary project | from that repo's `data/` folder |

The build fails loudly if either is missing, rather than silently producing a smaller game.

## Content filtering

The dictionaries are the *guess* lists, so anything left in them can be spelled out on the board.
Both languages run a profanity/slur filter, and **a self-test runs on every build** that fails the
build if a slur survives or an innocent word gets removed.

The interesting part is the false positives, because substring matching is unavoidable for
catching inflections. In English `rape` is inside *grape*, `arse` inside *coarse*, `turd` inside
*sturdy*. Arabic is worse because it glues prefixes and suffixes on: `لعن` appears inside
**طلعنا** ("we went out"), `غبي` inside **ترغبين** ("you want"), `سكس` inside **الكسكس**
(couscous). Those roots are matched whole-word only, and an allowlist rescues the rest.

## Licence / credits

Glossary content belongs to **ICAIRE** (International Center for AI Research and Ethics, under the
auspices of UNESCO). English word list: [dwyl/english-words](https://github.com/dwyl/english-words).
Arabic frequency list: [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords).
