"""
Command line runner for the Music Recommender Simulation.

Run with:  python -m src.main
"""

from src.recommender import load_songs, recommend_songs

# Default taste profile: an upbeat pop listener who prefers produced (non-acoustic) tracks.
# "genre", "mood", and "energy" drive the core score; "likes_acoustic" is a
# secondary signal that helps separate e.g. "intense rock" from "chill lofi".
DEFAULT_PROFILE = {
    "genre": "pop",
    "mood": "happy",
    "energy": 0.8,
    "likes_acoustic": False,
}


def print_recommendations(name: str, user_prefs: dict, recommendations: list) -> None:
    """Print a readable block of ranked recommendations with their reasons."""
    prefs = ", ".join(f"{k}={v}" for k, v in user_prefs.items())
    print("=" * 64)
    print(f"Profile: {name}")
    print(f"  ({prefs})")
    print("-" * 64)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']}, {song['mood']}]")
        print(f"   Score: {score:.2f} / 5.00")
        for reason in explanation.split("; "):
            print(f"     - {reason}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    recommendations = recommend_songs(DEFAULT_PROFILE, songs, k=5)
    print_recommendations("High-Energy Pop (default)", DEFAULT_PROFILE, recommendations)


if __name__ == "__main__":
    main()
