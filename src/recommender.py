import csv
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple, Union

# Point weights for the Algorithm Recipe (see README "How The System Works").
# The last five only apply when the user profile sets the matching preference.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre": 2.0,         # flat bonus for an exact genre match
    "mood": 1.0,          # flat bonus for an exact mood match
    "energy": 1.5,        # max points for energy closeness
    "acoustic": 0.5,      # max points for matching acoustic preference
    "decade": 0.5,        # exact decade = full, neighbouring decade = half
    "tags": 0.6,          # split evenly across up to TAGS_CAP matching mood tags
    "popularity": 0.3,    # mainstream hits vs. deep cuts
    "instrumental": 0.3,  # instrumental vs. vocal tracks
    "live": 0.2,          # live/room feel vs. clean studio sound
}
TAGS_CAP = 2

# Which user_prefs key switches on each weight (used to compute the max score).
PREF_FOR_WEIGHT = {
    "genre": "genre",
    "mood": "mood",
    "energy": "energy",
    "acoustic": "likes_acoustic",
    "decade": "decade",
    "tags": "mood_tags",
    "popularity": "likes_popular",
    "instrumental": "wants_instrumental",
    "live": "likes_live",
}

INT_FIELDS = {"id", "popularity", "release_decade"}
FLOAT_FIELDS = {
    "energy", "tempo_bpm", "valence", "danceability", "acousticness",
    "instrumentalness", "liveness",
}
LIST_FIELDS = {"mood_tags"}

# Diversity re-ranking penalties.
ARTIST_PENALTY = 1.0
GENRE_PENALTY = 0.5


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_decade: int = 2010
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    liveness: float = 0.0


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    favorite_decade: Optional[int] = None
    mood_tags: Optional[List[str]] = None
    likes_popular: Optional[bool] = None
    wants_instrumental: Optional[bool] = None
    likes_live: Optional[bool] = None

    def to_prefs(self) -> Dict:
        """Convert this profile into the user_prefs dict used by score_song."""
        prefs = {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
            "decade": self.favorite_decade,
            "mood_tags": self.mood_tags,
            "likes_popular": self.likes_popular,
            "wants_instrumental": self.wants_instrumental,
            "likes_live": self.likes_live,
        }
        return {k: v for k, v in prefs.items() if v is not None}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _fit(value: float, wants_high: bool) -> float:
    """Return value if the user wants it high, otherwise 1 - value."""
    return value if wants_high else 1 - value


def score_song(
    user_prefs: Dict, song: Dict, weights: Optional[Dict[str, float]] = None
) -> Tuple[float, List[str]]:
    """Score one song against user preferences, returning (score, reasons)."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    score = 0.0
    reasons: List[str] = []

    # Categorical matches: flat bonus, case-insensitive exact match.
    fav_genre = user_prefs.get("genre")
    if fav_genre and song["genre"].lower() == fav_genre.lower():
        score += w["genre"]
        reasons.append(f"genre match: {song['genre']} (+{w['genre']:.1f})")

    fav_mood = user_prefs.get("mood")
    if fav_mood and song["mood"].lower() == fav_mood.lower():
        score += w["mood"]
        reasons.append(f"mood match: {song['mood']} (+{w['mood']:.1f})")

    # Energy closeness: full points at the target, shrinking linearly with the gap.
    target = user_prefs.get("energy")
    if target is not None:
        gap = abs(song["energy"] - target)
        pts = w["energy"] * (1 - gap)
        score += pts
        reasons.append(
            f"energy {song['energy']:.2f} vs target {target:.2f} (+{pts:.2f})"
        )

    # Acoustic fit: reward acousticness if liked, otherwise reward produced sound.
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        pts = w["acoustic"] * _fit(song["acousticness"], likes_acoustic)
        score += pts
        label = "acoustic" if likes_acoustic else "produced"
        reasons.append(f"{label} sound fit (+{pts:.2f})")

    # --- Advanced features (only when the profile asks for them) ---

    decade = user_prefs.get("decade")
    if decade is not None and "release_decade" in song:
        diff = abs(song["release_decade"] - decade)
        if diff == 0:
            pts = w["decade"]
        elif diff == 10:
            pts = w["decade"] / 2
        else:
            pts = 0.0
        if pts:
            score += pts
            reasons.append(f"from the {song['release_decade']}s (+{pts:.2f})")

    wanted_tags = user_prefs.get("mood_tags")
    if wanted_tags and song.get("mood_tags"):
        song_tags = {t.lower() for t in song["mood_tags"]}
        hits = [t for t in wanted_tags if t.lower() in song_tags][:TAGS_CAP]
        if hits:
            pts = w["tags"] / TAGS_CAP * len(hits)
            score += pts
            reasons.append(f"mood tags: {', '.join(hits)} (+{pts:.2f})")

    likes_popular = user_prefs.get("likes_popular")
    if likes_popular is not None and "popularity" in song:
        pts = w["popularity"] * _fit(song["popularity"] / 100, likes_popular)
        score += pts
        label = "popular hit" if likes_popular else "deep cut"
        reasons.append(f"{label}, popularity {song['popularity']} (+{pts:.2f})")

    wants_instrumental = user_prefs.get("wants_instrumental")
    if wants_instrumental is not None and "instrumentalness" in song:
        pts = w["instrumental"] * _fit(song["instrumentalness"], wants_instrumental)
        score += pts
        label = "instrumental" if wants_instrumental else "vocal"
        reasons.append(f"{label} fit (+{pts:.2f})")

    likes_live = user_prefs.get("likes_live")
    if likes_live is not None and "liveness" in song:
        pts = w["live"] * _fit(song["liveness"], likes_live)
        score += pts
        label = "live feel" if likes_live else "studio polish"
        reasons.append(f"{label} fit (+{pts:.2f})")

    return round(score, 2), reasons


def max_score(user_prefs: Dict, weights: Optional[Dict[str, float]] = None) -> float:
    """Return the best score possible for this profile under these weights."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    return sum(
        w[name] for name, pref in PREF_FOR_WEIGHT.items()
        if user_prefs.get(pref) not in (None, "", [])
    )


# ---------------------------------------------------------------------------
# Scoring modes (Strategy pattern)
# ---------------------------------------------------------------------------

class ScoringStrategy:
    """A named, swappable scoring mode: same algorithm, different priorities."""

    def __init__(self, name: str, description: str, weights: Dict[str, float]):
        """Store the mode's name, a one-line description, and its weight overrides."""
        self.name = name
        self.description = description
        self.weights = {**DEFAULT_WEIGHTS, **weights}

    def score(self, user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
        """Score a song using this strategy's weights."""
        return score_song(user_prefs, song, self.weights)

    def max_score(self, user_prefs: Dict) -> float:
        """Best possible score for this profile under this strategy."""
        return max_score(user_prefs, self.weights)


STRATEGIES: Dict[str, ScoringStrategy] = {
    "genre-first": ScoringStrategy(
        "genre-first", "Default recipe: genre is the strongest signal.", {}
    ),
    "mood-first": ScoringStrategy(
        "mood-first",
        "Mood beats genre: good for 'I just want something happy'.",
        {"genre": 1.0, "mood": 2.0, "tags": 1.0},
    ),
    "energy-focused": ScoringStrategy(
        "energy-focused",
        "Match the intensity first (workouts, focus sessions).",
        {"genre": 0.5, "mood": 0.5, "energy": 3.0},
    ),
}


def get_strategy(
    mode: Union[str, ScoringStrategy, None] = None,
    weights: Optional[Dict[str, float]] = None,
) -> ScoringStrategy:
    """Resolve a mode name, strategy object, or raw weights into a strategy."""
    if isinstance(mode, ScoringStrategy):
        return mode
    if weights is not None:
        return ScoringStrategy("custom", "Custom weights.", weights)
    name = mode or "genre-first"
    if name not in STRATEGIES:
        raise ValueError(f"Unknown mode '{name}'. Choose from: {', '.join(STRATEGIES)}")
    return STRATEGIES[name]


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def _diversify(
    scored: List[Tuple[Dict, float, List[str]]], k: int
) -> List[Tuple[Dict, float, List[str]]]:
    """Greedily pick k songs, penalizing artists/genres already chosen."""
    remaining = list(scored)
    chosen: List[Tuple[Dict, float, List[str]]] = []
    while remaining and len(chosen) < k:
        best_i, best = 0, None
        for i, (song, score, reasons) in enumerate(remaining):
            penalty, notes = 0.0, []
            if any(c[0]["artist"] == song["artist"] for c in chosen):
                penalty += ARTIST_PENALTY
                notes.append(f"diversity: artist already listed (-{ARTIST_PENALTY:.1f})")
            if any(c[0]["genre"] == song["genre"] for c in chosen):
                penalty += GENRE_PENALTY
                notes.append(f"diversity: genre already listed (-{GENRE_PENALTY:.1f})")
            candidate = (song, round(score - penalty, 2), reasons + notes)
            if best is None or candidate[1] > best[1]:
                best_i, best = i, candidate
        chosen.append(best)
        remaining.pop(best_i)
    return chosen


def rank_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: Optional[ScoringStrategy] = None,
    diverse: bool = False,
) -> List[Tuple[Dict, float, List[str]]]:
    """Score and sort every song, returning (song, score, reasons) for the top k."""
    strategy = strategy or get_strategy()
    target = user_prefs.get("energy", 0.5)
    scored = [(song, *strategy.score(user_prefs, song)) for song in songs]
    # Tie-break by the smaller energy gap so closer-vibe songs win ties.
    scored.sort(key=lambda item: (-item[1], abs(item[0]["energy"] - target)))
    return _diversify(scored, k) if diverse else scored[:k]


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: Optional[Dict[str, float]] = None,
    mode: Union[str, ScoringStrategy, None] = None,
    diverse: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort highest first, and return the top-k with explanations."""
    strategy = get_strategy(mode, weights)
    ranked = rank_songs(user_prefs, songs, k, strategy, diverse)
    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked]


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(
        self,
        songs: List[Song],
        weights: Optional[Dict[str, float]] = None,
        mode: Union[str, ScoringStrategy, None] = None,
        diverse: bool = False,
    ):
        """Store the catalog, the scoring strategy, and the diversity setting."""
        self.songs = songs
        self.strategy = get_strategy(mode, weights)
        self.diverse = diverse

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects for the user, highest score first."""
        by_id = {s.id: s for s in self.songs}
        ranked = rank_songs(
            user.to_prefs(), [asdict(s) for s in self.songs], k, self.strategy, self.diverse
        )
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable sentence explaining a song's score for the user."""
        score, reasons = self.strategy.score(user.to_prefs(), asdict(song))
        return f"Score {score:.2f}: " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Read the songs CSV into a list of dicts with numeric fields converted."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in INT_FIELDS & row.keys():
                row[key] = int(row[key])
            for key in FLOAT_FIELDS & row.keys():
                row[key] = float(row[key])
            for key in LIST_FIELDS & row.keys():
                row[key] = [t.strip() for t in row[key].split(";") if t.strip()]
            songs.append(row)
    print(f"Loaded songs: {len(songs)}")
    return songs
