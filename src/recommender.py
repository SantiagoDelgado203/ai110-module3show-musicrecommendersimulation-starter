import csv
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

# Point weights for the Algorithm Recipe (see README "How The System Works").
DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre": 2.0,     # flat bonus for an exact genre match
    "mood": 1.0,      # flat bonus for an exact mood match
    "energy": 1.5,    # max points for energy closeness
    "acoustic": 0.5,  # max points for matching acoustic preference
}

INT_FIELDS = {"id"}
FLOAT_FIELDS = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}


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

    def to_prefs(self) -> Dict:
        """Convert this profile into the user_prefs dict used by score_song."""
        return {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "likes_acoustic": self.likes_acoustic,
        }


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], weights: Optional[Dict[str, float]] = None):
        """Store the song catalog and the scoring weights to use."""
        self.songs = songs
        self.weights = weights or DEFAULT_WEIGHTS

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects for the user, highest score first."""
        prefs = user.to_prefs()
        ranked = sorted(
            self.songs,
            key=lambda s: score_song(prefs, asdict(s), self.weights)[0],
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a readable sentence explaining a song's score for the user."""
        score, reasons = score_song(user.to_prefs(), asdict(song), self.weights)
        return f"Score {score:.2f}: " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Read the songs CSV into a list of dicts with numeric fields converted."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field in INT_FIELDS:
                row[field] = int(row[field])
            for field in FLOAT_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    print(f"Loaded songs: {len(songs)}")
    return songs


def score_song(
    user_prefs: Dict, song: Dict, weights: Optional[Dict[str, float]] = None
) -> Tuple[float, List[str]]:
    """Score one song against user preferences, returning (score, reasons)."""
    w = weights or DEFAULT_WEIGHTS
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
        fit = song["acousticness"] if likes_acoustic else 1 - song["acousticness"]
        pts = w["acoustic"] * fit
        score += pts
        label = "acoustic" if likes_acoustic else "produced"
        reasons.append(f"{label} sound fit (+{pts:.2f})")

    return round(score, 2), reasons


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[Dict, float, str]]:
    """Score every song, sort highest first, and return the top-k with explanations."""
    target = user_prefs.get("energy", 0.5)
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, "; ".join(reasons)))
    # Tie-break by the smaller energy gap so closer-vibe songs win ties.
    scored.sort(key=lambda item: (-item[1], abs(item[0]["energy"] - target)))
    return scored[:k]
