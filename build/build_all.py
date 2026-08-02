# -*- coding: utf-8 -*-
import json, re, os, sys
BASE = os.path.dirname(os.path.abspath(__file__)) + os.sep

# glossary.json is not committed (it belongs to the AI-Glossary-Challenge-by-ICAIRE project).
# Drop it next to this script, or point ICAIRE_GLOSSARY at it.
GLOSSARY = os.environ.get("ICAIRE_GLOSSARY") or (BASE + "glossary.json")
if not os.path.exists(GLOSSARY):
    sys.exit("glossary.json not found at %s\n"
             "Copy it next to this script, or set ICAIRE_GLOSSARY=/path/to/glossary.json" % GLOSSARY)
data = json.load(open(GLOSSARY, encoding="utf-8"))

# ================= ENGLISH =================
EN_KEEP = set("""AGENT ACTION BATCH CHATBOT CLASS CLUSTER CORPUS DECODER DEPTH ENCODER
ENTITY EPOCH EXAMPLE FEATURE FRAME KERNEL LABEL LAMBDA LATENCY LAYER METRIC MODEL
NEURON OBJECT OUTLIER PADDING PANDAS POLICY PRIVACY PROMPT PYTHON RECALL RETURN
REWARD ROBOT SAFETY SAMPLE SCORING SYNAPSE SYSTEM TENSOR TOKEN TORCH TRUST WEIGHT""".split())
en = {}
for e in data:
    t = e.get('english_term','').strip().upper()
    if t in EN_KEEP and t not in en:
        d = re.sub(r'\s+',' ', e.get('english_def','').strip())
        d = re.sub(r'^[^A-Za-z0-9"(]+','', d)
        en[t] = {'def': d, 'tr': e.get('arabic_term','').strip()}   # tr = Arabic equivalent

# ================= PROFANITY / SLUR BLOCKLIST =================
# The dictionaries are the *guess* lists — anything in them is accepted as a typed word and
# painted onto the board. Slurs and cusses must never survive here. Over-filtering only costs
# a rejected probe word; under-filtering puts a slur on screen in a UNESCO-affiliated demo.
#
# STEMS are substring matches (they catch inflections automatically) and are chosen so they
# cannot hit an innocent word. EXACT is for words whose letters DO occur inside innocent ones
# — "rape" is inside "grape"/"scrape", "arse" inside "coarse"/"sparse", "coon" inside
# "raccoon"/"tycoon", "spic" inside "spice" — so those must never be used as stems.
EN_STEMS = """fuck shit bitch cunt whore slut nigg faggot fagot retard wank twat turd jizz
bollock bugger dildo prick pussy pussi queef felch skank tosser minge munter cocksuck
motherfuck douche bastard asshole arsehole shithead dumbass jackass smartass bullshit
clitor titt bimbo floozy hussy wetback raghead""".split()
EN_EXACT = """arse arses arsed asses coon coons spic spics chink chinks gook gooks dago dagos
rape raped rapes raper rapers raping rapist kike kikes dyke dykes homos fags queer queers
tranny darkie darky negro negros negroes honky honkie honkies paki pakis beaner sambo
mulatto gypsy gypsys gypsies cripple midget midgets spastic spazz spaz moron morons idiot
idiots cretin cretins dunce dunces stupid stupidly imbecil cocks dicks dicked goddam goddamn
crap craps crappy crapped piss pissed pisses pisser hooker hookers boobs boobies knobhead
loser losers scumbag""".split()
# Innocent words the stems would otherwise swallow: STURDY contains "turd", SWANK/WANKEL
# contain "wank", MISHIT/WASHITA/CUSHITE contain "shit", PRICKLY contains "prick".
# This allowlist wins over the stems (but never over EN_EXACT).
EN_ALLOW = """sturdy swank swanks swanked swanker swankey swankie swanky twank twanky
twankay twanker twankle mishit mishits washita peshito cushite prickle prickly pricked
pricker pricket wankel titter titters tittery tittle tittles tittler tittlin tittup
tittups tittupy turdus turdine turdoid""".split()

EN_BLOCK = set(w.upper() for w in EN_EXACT)
EN_ALLOW = set(w.upper() for w in EN_ALLOW)
EN_STEMS = [s.upper() for s in EN_STEMS]

def en_clean(w):
    if w in EN_BLOCK: return False
    if w in EN_ALLOW: return True
    for s in EN_STEMS:
        if s in w: return False
    return True

raw = open(BASE + "words_alpha.txt", encoding="utf-8").read().split()
WORD_RE = re.compile(r'^[a-z]{5,7}$')
en_all = set(w.upper() for w in raw if WORD_RE.match(w))
en_dict = set(w for w in en_all if en_clean(w))
en_blocked = len(en_all) - len(en_dict)
# answer terms are curated AI glossary words; make sure the filter never eats one
for t in en:
    assert en_clean(t), "blocklist would remove the answer word " + t
en_dict |= set(en.keys())

# ================= ARABIC (all \u escapes for marks/ranges to dodge bidi reordering) =================
TASHKEEL = re.compile('[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')  # tashkeel; \u escapes on purpose
def strip_diac(s): return TASHKEEL.sub('', s.replace('\u0640', ''))  # 0640 = tatweel
NORM = {'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا',  # alef->ا
        'ة':'ه','ى':'ي','ؤ':'و','ئ':'ي'}   # ة->ه ى->ي ؤ->و ئ->ي
def normalize(s): return ''.join(NORM.get(c,c) for c in s)
ARABIC_RE = re.compile('^[\u0621-\u064A]+$')  # hamza .. yeh

AR_CONCEPTS = set(x.lower() for x in """system model agent data robot training
classification example layer epoch token entity policy metric boosting optimization
frame corpus gradient variance probability regression correlation scoring parameter
transformer classifier filter lambda tensor generalization convergence iteration user
safety privacy hypothesis sample kernel python prediction embedding chunking pruning
reward return unit label""".split())
ar = {}                 # keyed by REAL (diacritic-stripped) spelling -> def
seen_norm = set()
for e in data:
    en_term = e.get('english_term','').strip().lower()
    src = strip_diac(e.get('arabic_term','').strip())
    if en_term in AR_CONCEPTS and ARABIC_RE.match(src) and 4 <= len(src) <= 6:
        nk = normalize(src)
        if nk not in seen_norm:
            seen_norm.add(nk)
            ar[src] = {'def': re.sub(r'\s+',' ', e.get('arabic_def','').strip()),
                       'tr': e.get('english_term','').strip()}

# Arabic cusses / insults / slurs. Compared after normalize(strip_diac(...)), the same form
# the dict is stored in, so spelling variants (أ/ا, ة/ه, ى/ي) all collapse onto one entry.
# NOTE: "شاذ" is deliberately absent — it is a real glossary term (قيمة شاذة = outlier).
# AR_STEMS are substring matches, so they catch ال/ة/ات/ين inflections automatically. Each one
# was checked against ordinary words first. AR_EXACT is for roots whose letters DO occur inside
# innocent words and must therefore match whole-word only — verified collisions:
#   ابله in قابله/مقابله    معاق in معاقبة     معوق in معوقات    نيك in تكنيك/بيكنيك
#   خرا in إخراج/خراج       زنا in زناد        خول in دخول       كس in كسر/مكسور
#   لعن in طلعنا  <- this one is why ملعون is a stem but لعن is not
AR_STEMS = """حمار حمير جحش بهيمه خنزير خنازير كلب كلاب
احمق حمقى مغفل هبيل مجنون تافه سخيف متخلف بليد غبي
حقير سافل وقح خسيس نذل قذر وسخ نجس زباله ملعون
عاهر قحب شرموط فاسق داعر ديوث طيز متناك""".split()
# Whole-word only. Either the letters appear inside ordinary words (see the collisions above),
# or the root collided with too much to be a safe stem — every one of these was found in the
# real dictionary: بغل in بغلق/بغلطة/بغلاف, زاني in أحزاني/خزاني, لوطي in الوطيس,
# معتوه in سمعتوه, منيك in دومنيك (the name), سكس in الكسكس/ساسكس/سكسوكة (goatee).
AR_EXACT = """ابله بلهاء معاق معوق نيك ينيك خرا خره زنا خول عرص كس زب
لعنه يلعن العن اغبى اغبي
بغل البغل بغله بغال زاني زانيه الزاني زانيا زانيات
لوطي اللوطي لوطيا لوطيه لوطيين معتوه معتوهه معتوها المعتوه معتوهين
منيك منيوك منيكه سكس سكسي سكسيه""".split()
# Innocent words the remaining stems would still swallow — substring exceptions, because Arabic
# glues prefixes/suffixes on: رغب covers ترغبين/راغبين/ترغبي (غبي), اكتاف covers أكتافه (تافه),
# تخسيس is slimming (خسيس). These win over the stems but never over AR_EXACT.
# راغب needs its own entry: راغبين is ر-ا-غ-ب, so the رغب exception does not reach it. And it
# must NOT be shortened to اغب — that substring also appears in اغبياء, which must stay blocked.
AR_ALLOW = """رغب راغب اكتاف تخسيس بليدس""".split()

AR_STEMS = [normalize(strip_diac(w)) for w in AR_STEMS]
AR_ALLOW = [normalize(strip_diac(w)) for w in AR_ALLOW]
AR_BLOCK = set(normalize(strip_diac(w)) for w in AR_EXACT)

def ar_clean(w):                      # w is already normalize(strip_diac(...))'d
    if w in AR_BLOCK: return False
    for a in AR_ALLOW:
        if a in w: return True
    for s in AR_STEMS:
        if s in w: return False
    return True

# Source: hermitdave/FrequencyWords ar_full (2018) — 2.5M entries, "word count" per line.
# The old ar_50k list only yielded 28.5k playable words, which rejected far too much real
# Arabic typing next to English's 87.6k. AR_FREQ_MIN trims the long tail: this is a
# subtitle corpus, so rare entries are largely typos, dialect and transliterations.
# 32 lands the dictionary at ~88k, matching the English side.
AR_FREQ_MIN = 32
ar_freq = {}
for line in open(BASE + "ar_full_raw.txt", encoding="utf-8"):
    parts = line.split()
    if len(parts) != 2: continue
    try: n = int(parts[1])
    except ValueError: continue
    w = strip_diac(parts[0])
    if ARABIC_RE.match(w) and 4 <= len(w) <= 6:
        k = normalize(w)                       # variants collapse, so sum their counts
        ar_freq[k] = ar_freq.get(k, 0) + n
ar_all = set(w for w, n in ar_freq.items() if n >= AR_FREQ_MIN)
MANUAL = ["توكن", "داتا"]  # توكن, داتا
for w in MANUAL:
    if 4 <= len(w) <= 6: ar_all.add(normalize(w))

ar_dict = set(w for w in ar_all if ar_clean(w))
ar_blocked = len(ar_all) - len(ar_dict)
for k in ar:                                  # never let the filter eat an answer
    assert ar_clean(normalize(k)), "blocklist would remove the answer word " + k
ar_dict |= set(normalize(k) for k in ar.keys())

# ================= EMIT =================
with open(BASE+"en_words.txt","w",encoding="utf-8") as f:
    f.write('\n'.join('    %s: { def: %s, tr: %s },' % (w, json.dumps(en[w]["def"], ensure_ascii=False), json.dumps(en[w]["tr"], ensure_ascii=False)) for w in sorted(en)))
with open(BASE+"ar_words.txt","w",encoding="utf-8") as f:
    f.write('\n'.join('    "%s": { def: %s, tr: %s },' % (w, json.dumps(ar[w]["def"], ensure_ascii=False), json.dumps(ar[w]["tr"], ensure_ascii=False)) for w in sorted(ar)))
with open(BASE+"en_dict.txt","w",encoding="utf-8") as f:
    f.write(' '.join(sorted(en_dict)))
with open(BASE+"ar_dict.txt","w",encoding="utf-8") as f:
    f.write(' '.join(sorted(ar_dict)))

print("EN answers:", len(en), "| EN dict:", len(en_dict), "| blocked:", en_blocked)
print("AR answers:", len(ar), "| AR dict:", len(ar_dict), "| blocked:", ar_blocked)
print("AR answer sample:", ', '.join(list(sorted(ar))[:8]))
for w in ["كلمة","نموذج","بيانات","توكن","داتا","زززز"]:
    print("  guess", w, "->", "valid" if normalize(strip_diac(w)) in ar_dict else "INVALID")

# ---- filter self-test: runs on every build so a regression can't slip through ----
MUST_BLOCK_EN = "FUCKS FUCKED SHITS SHITTY BITCH BITCHES WHORE SLUTS CUNTS NIGGER NIGGAS " \
    "FAGGOT RETARD RETARDS BASTARD ASSHOLE PRICKS WANKER TWATS PISSED CHINK COONS SPICS " \
    "RAPIST RAPED DYKES CRIPPLE MIDGET MORONS IDIOTS STUPID CRAPPY NEGRO GYPSY".split()
MUST_KEEP_EN = "GRAPES SCRAPE COARSE SPARSE PARSES RACCOON COCOON TYCOON SPICE SPICY " \
    "HOARSE PEACOCK CLASSIC ASSETS ASSIST MASSES PASSES GLASSY BUTTON COTTON TITLE " \
    "KITTEN ANALYST OUTLIER PYTHON TENSOR STURDY SWANKY MISHIT PRICKLY WANKEL " \
    "CUSHITE TITTER DICKEY".split()
MUST_BLOCK_AR = """حمار حماره حمير ابله معاق معوق غبي غبيه اغبياء احمق خنزير خنازير
حقير قذر خول طيز كلاب قحبه عاهره شرموطه لوطي ملعون متخلف سافل مجنون""".split()
# innocent words that the substring stems would eat if a root were mis-scoped — طلعنا is why
# لعن is exact-only, معاقبه/معوقات/قابله/تكنيك/اخراج/زناد/دخول/كسر are the other collisions
MUST_KEEP_AR  = "بيانات نموذج فرضية كلمة تدريب طبقة عينة".split()
# Innocent words the substring stems would eat if a root were mis-scoped. Asserted against the
# FILTER, not against the dictionary: absence from the dict can also mean "below AR_FREQ_MIN" or
# "not 4-6 letters" (طلعنا appears 8x, تكنيك 26x, كسر is 3 letters) — that is not a filter bug.
AR_NOT_BLOCKED = """طلعنا معاقبه معوقات قابله مقابله تكنيك بيكنيك اخراج خراج زناد دخول مدخول كسر مكسور شاذ
ترغبين ترغبي راغبين الرغبي اكتافه الوطيس سمعتوه تخسيس الكسكس ساسكس سكسوكه دومنيك
بغلق بغلطه بغلاف احزاني خزاني""".split()

bad = [w for w in MUST_BLOCK_EN if w in en_dict] \
    + [w for w in MUST_KEEP_EN if w not in en_dict] \
    + [w for w in MUST_BLOCK_AR if normalize(strip_diac(w)) in ar_dict] \
    + [w for w in MUST_KEEP_AR  if normalize(strip_diac(w)) not in ar_dict] \
    + [w for w in AR_NOT_BLOCKED if not ar_clean(normalize(strip_diac(w)))]
if bad:
    raise SystemExit("WORDLIST SELF-TEST FAILED for: " + ", ".join(bad))
print("wordlist self-test: OK  (%d EN + %d AR cases)" %
      (len(MUST_BLOCK_EN) + len(MUST_KEEP_EN), len(MUST_BLOCK_AR) + len(MUST_KEEP_AR) + len(AR_NOT_BLOCKED)))
