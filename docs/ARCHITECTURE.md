# How Promptle works

## Two stages

Nothing is computed at run time that could be computed ahead of time.

```
BUILD TIME (python, once)                    RUN TIME (browser)
glossary.json  (1,242 terms)
words_alpha.txt (~370k words)  -> build_all.py -> 4 data files
ar_full_raw.txt (2.5M entries)                       |
                                                 inject.py
                                                     |
                                              index.html (one file)
```

The browser receives ~88k English and ~88k Arabic words as one space-separated string, which
becomes a `Set` at boot — lookups are then O(1) with no network. That is why the file is ~1.7 MB
and why it works offline, from a `file://` double-click, or embedded in a page.

**Edit `game_template.html` for behaviour, `build_all.py` for data.** Never edit `index.html`;
it is generated and your changes will be overwritten on the next build.

## Choosing the daily word

No server decides it. It is arithmetic:

```js
function dayNumber() {
  var d = new Date();
  var today = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
  return Math.floor((today - Date.UTC(2026, 0, 1)) / 86400000);
}
answer = sortedKeys[ dayNumber() % keys.length ];
```

Two details that matter:

- `Date.UTC` is applied to the **local** calendar date. It is only used to get a clean day count
  free of daylight-saving hours — not to switch the game to UTC.
- `keys.sort()` — object key order isn't guaranteed, so sorting keeps the sequence stable. Without
  it, a rebuild could silently reshuffle everyone's word.

## The lock is a key, not a timer

The word is *derived*; the lock is *memory*. Guesses are saved under a key like
`promptle.2026-7-25.en`. Tomorrow the key changes, so yesterday's finished game is simply never
looked up again — which is why the lock expires at local midnight with no countdown anywhere.

On load, saved guesses are replayed and re-scored without animation, restoring the board.

Practice mode bypasses both halves: a random word instead of the date-derived one, and
`saveState()` / `recordResult()` return early so it can never touch the daily state or the stats.

## Scoring — the part clones get wrong

```js
var res = new Array(cols).fill("absent");
var pool = ans.split("").map(normChar);

// pass 1: exact positions
for (i) if (g[i] === pool[i]) { res[i] = "correct"; pool[i] = null; }

// pass 2: wrong position, from what's left
for (j) { if (res[j] === "correct") continue;
          var idx = pool.indexOf(g[j]);
          if (idx > -1) { res[j] = "present"; pool[idx] = null; } }
```

Two passes, and each answer letter is nulled once consumed. This is entirely about **duplicate
letters**: answer `PADDING`, guess `DIAGRAM`. Scoring left-to-right in one pass, the first `D`
would consume a `D` and you'd have no way to know whether the second should be amber. Consuming
exact matches first, and letting each answer letter be claimed only once, is what makes "one
amber D" mean "there is exactly one more D you haven't placed".

## Keyboard memory

`updateKey()` uses a rank so a key never downgrades:

```js
var RANK = { absent: 0, present: 1, correct: 2 };
if (prev && RANK[prev] >= RANK[state]) return;
```

`keyState` is also the record of what the player has discovered, which is what makes the hint
honest: it filters the answer's letters down to those with no `keyState` entry and picks only from
those. If every letter is already known it says so and does **not** spend the hint.

The hint persists as `state.hint` — the actual letter, not a boolean. Storing only a flag would be
worse than not persisting at all: on reload you'd lose the hint *and* the information it gave you.

## Arabic

Three real mechanisms, not a translation layer:

- **Forgiving matching.** `AR_NORM` collapses أ/إ/آ→ا, ة→ه, ى→ي, ؤ→و, ئ→ي. The board shows what you
  typed; validation and scoring compare normalized forms. The same map runs at build time so both
  sides agree.
- **RTL is a direction, not a reversal.** `dir="rtl"` on the wrapper; everything inherits. Adding
  `flex-direction: row-reverse` on top of that double-flips and reverses reading order — a real
  bug that shipped once. The **keyboard** is deliberately forced back to `ltr`, because it depicts
  a physical Arabic 101 board where ض sits on the Q key, at the far left.
- **Diacritics** are stripped at build time. The regex ranges use `\u` escapes on purpose: literal
  combining marks get bidi-reordered when written to a file and silently corrupt the character
  class, which has broken this pipeline more than once.

## Layout

`tileSize()` measures — it does not guess. It reads the wrapper's real content width (the same box
the keyboard rows span, so the board's edges line up with the clue card) and subtracts the measured
height of the header, clue, message and keyboard. Three things it must keep doing:

1. **Guard implausible measurements.** The game can be laid out while hidden inside an iframe; a
   truthy-but-tiny `clientWidth` would otherwise lock the board at its 28px minimum.
2. **Watch the element, not the window** (`ResizeObserver`) — the window doesn't resize when a
   container reveals the game.
3. **Recompute twice** (150ms and 500ms). A single debounced pass can land mid-layout and latch an
   intermediate size.

On mobile the tile size is limited by **width**, never height — 7 tiles across ~375px — so the only
lever for bigger squares is trimming page padding and gaps, which a `max-width:480px` block does.
