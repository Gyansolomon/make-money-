"""The words of "The Trees Nobody Planted" and where they sit in the song.

text: what appears on screen. say: what Kokoro reads (decades spelled out).
section: starts a new section of the arrangement at this line's bar.
bar: earliest bar for the line; on: "bar" snaps to a downbeat, "beat" to the next beat.
rest: minimum beats of silence after the previous line.

Facts (checked Sept 2026, see research/scripts/trees-nobody-planted.md): Sahel drought from the
late 1960s, worst in the early 1970s, again in the 1980s; Tony Rinaudo's discovery in Niger in
1983; farmer-managed natural regeneration brought back ~200 million trees on ~5 million hectares,
enough extra food for ~2.5 million people.
"""

BPM = 100
SR = 24000

# Kokoro's default phonemes, corrected: Niger the country (nee-ZHAIR) and Rinaudo (rih-NOH-doh)
PRONOUNCE = {"nˈaɪdʒɚ": "niːʒˈɛɹ", "ɹɪnˈɔːdoʊ": "ɹɪnˈoʊdoʊ"}

LINES = [
    # intro: the number first
    {"text": "Two hundred million trees.", "say": "Two hundred million trees.", "bar": 1, "section": "intro"},
    {"text": "In one of the driest places on Earth.", "say": "In one of the driest places on Earth."},
    {"text": "And nobody planted them.", "say": "And nobody planted them.", "section": "hook1"},
    # verse 1: the trees come down
    {"text": "Niger. The 1970s.", "say": "Niger. The nineteen seventies.", "rest": 2, "section": "verse1"},
    {"text": "The edge of the Sahara.", "say": "The edge of the Sahara."},
    {"text": "Millet in the fields, old trees in between.", "say": "Millet in the fields, old trees in between."},
    {"text": "More people every year. More fields. More firewood.", "say": "More people every year. More fields. More firewood."},
    {"text": "So the trees come down.", "say": "So the trees come down."},
    {"text": "Problem solved.", "say": "Problem solved.", "on": "beat"},
    {"text": "Well. Not exactly.", "say": "Well. Not exactly.", "on": "beat", "rest": 1},
    # verse 2: the drought
    {"text": "Those roots were holding the soil together.", "say": "Those roots were holding the soil together.", "section": "verse2"},
    {"text": "That shade was keeping the crops alive.", "say": "That shade was keeping the crops alive."},
    {"text": "Then the rain stops.", "say": "Then the rain stops."},
    {"text": "The wind takes the soil. The crops die. The cattle die.", "say": "The wind takes the soil. The crops die. The cattle die.", "rest": 2, "section": "break"},
    {"text": "And the desert keeps moving south.", "say": "And the desert keeps moving south."},
    # verse 3: planting fails
    {"text": "So the world does what it always does.", "say": "So the world does what it always does.", "section": "verse3"},
    {"text": "Plant trees! Millions of seedlings.", "say": "Plant trees! Millions of seedlings."},
    {"text": "Almost all of them die.", "say": "Almost all of them die.", "speed": 0.95},
    # bridge: the discovery
    {"text": "1983.", "say": "Nineteen eighty-three.", "rest": 2, "section": "bridge"},
    {"text": "Tony Rinaudo is ready to go home.", "say": "Tony Rinaudo is ready to go home."},
    {"text": "He looks down at a scruffy little bush,", "say": "He looks down at a scruffy little bush,"},
    {"text": "and it isn’t a bush.", "say": "and it isn't a bush.", "speed": 0.95, "section": "riser"},
    # drop: the forest underground
    {"text": "It’s a tree. Cut down years ago.", "say": "It's a tree. Cut down years ago.", "section": "drop"},
    {"text": "The roots are still alive.", "say": "The roots are still alive."},
    {"text": "A whole forest, hiding underground.", "say": "A whole forest, hiding underground."},
    {"text": "So the farmers stop cutting, and start choosing.", "say": "So the farmers stop cutting, and start choosing.", "section": "regrow"},
    {"text": "One strong shoot per stump. Let it grow.", "say": "One strong shoot per stump. Let it grow."},
    {"text": "Twenty years later: two hundred million trees.", "say": "Twenty years later. Two hundred million trees."},
    {"text": "Food for two and a half million more people.", "say": "Food for two and a half million more people."},
    {"text": "And nobody planted them.", "say": "And nobody planted them.", "rest": 2, "section": "hook2"},
]
