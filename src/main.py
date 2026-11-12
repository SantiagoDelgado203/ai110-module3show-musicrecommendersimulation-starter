"""
Command line runner for the Music Recommender Simulation.

Run with:  python -m src.main
"""

from src.recommender import DEFAULT_WEIGHTS, load_songs, recommend_songs

# Default taste profile: an upbeat pop listener who prefers produced (non-acoustic) tracks.
# "genre", "mood", and "energy" drive the core score; "likes_acoustic" is a
# secondary signal that helps separate e.g. "intense rock" from "chill lofi".
DEFAULT_PROFILE = {
    "genre": "pop",
    "mood": "happy",
    "energy": 0.8,
    "likes_acoustic": False,
}


# Stress-test profiles: three "normal" listeners plus adversarial / edge cases.
PROFILES = {
    "High-Energy Pop (default)": DEFAULT_PROFILE,
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
    # Edge case: conflicting signals, very high energy but a sad mood.
    "Conflicted (energy 0.9 + sad)": {"genre": "folk", "mood": "sad", "energy": 0.9, "likes_acoustic": True},
    # Edge case: genre that does not exist in the catalog.
    "Unknown Genre (k-pop)": {"genre": "k-pop", "mood": "happy", "energy": 0.7, "likes_acoustic": False},
    # Edge case: dead-center energy and no strong preferences.
    "Middle-of-the-Road": {"genre": "jazz", "mood": "romantic", "energy": 0.5, "likes_acoustic": True},
}

# Experiment: "Weight Shift" - double energy, halve genre.
EXPERIMENT_WEIGHTS = {"genre": 1.0, "mood": 1.0, "energy": 3.0, "acoustic": 0.5}


def print_recommendations(
    name: str, user_prefs: dict, recommendations: list, weights: dict = DEFAULT_WEIGHTS
) -> None:
    """Print a readable block of ranked recommendations with their reasons."""
    prefs = ", ".join(f"{k}={v}" for k, v in user_prefs.items())
    print("=" * 64)
    print(f"Profile: {name}")
    print(f"  ({prefs})")
    print("-" * 64)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']}, {song['mood']}]")
        print(f"   Score: {score:.2f} / {sum(weights.values()):.2f}")
        for reason in explanation.split("; "):
            print(f"     - {reason}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    for name, prefs in PROFILES.items():
        print_recommendations(name, prefs, recommend_songs(prefs, songs, k=5))

    print("#" * 64)
    print("EXPERIMENT: Weight Shift (genre 2.0 -> 1.0, energy 1.5 -> 3.0)")
    print("#" * 64)
    for name in ("High-Energy Pop (default)", "Conflicted (energy 0.9 + sad)"):
        prefs = PROFILES[name]
        recs = recommend_songs(prefs, songs, k=5, weights=EXPERIMENT_WEIGHTS)
        print_recommendations(f"{name} [weight shift]", prefs, recs, EXPERIMENT_WEIGHTS)


if __name__ == "__main__":
    main()
