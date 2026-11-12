"""
Command line runner for the Music Recommender Simulation.

Run with:  python -m src.main            (all profiles + weight-shift experiment)
Options:   --profile NAME   only run one profile (see --list)
           --mode MODE      genre-first | mood-first | energy-focused
           --diverse        penalize repeated artists/genres in the top k
           --table          print an ASCII summary table instead of lists
           --compare-modes  run the profile(s) under every scoring mode
           --list           list profile names and scoring modes
"""

import argparse
import textwrap
from typing import Dict, List

from src.recommender import (
    STRATEGIES,
    get_strategy,
    load_songs,
    max_score,
    recommend_songs,
)

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
    # Uses the advanced features (decade, mood tags, popularity, instrumental, live).
    "Nostalgic Storyteller": {
        "genre": "country",
        "mood": "nostalgic",
        "energy": 0.5,
        "likes_acoustic": True,
        "decade": 1970,
        "mood_tags": ["storytelling", "warm"],
        "likes_popular": False,
        "wants_instrumental": False,
        "likes_live": True,
    },
}

# Experiment: "Weight Shift" - double energy, halve genre.
EXPERIMENT_WEIGHTS = {"genre": 1.0, "mood": 1.0, "energy": 3.0, "acoustic": 0.5}


def print_recommendations(
    name: str, user_prefs: dict, recommendations: list, weights: dict = None
) -> None:
    """Print a readable block of ranked recommendations with their reasons."""
    prefs = ", ".join(f"{k}={v}" for k, v in user_prefs.items())
    best = max_score(user_prefs, weights)
    print("=" * 64)
    print(f"Profile: {name}")
    print(f"  ({prefs})")
    print("-" * 64)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']}, {song['mood']}]")
        print(f"   Score: {score:.2f} / {best:.2f}")
        for reason in explanation.split("; "):
            print(f"     - {reason}")
    print()


def format_table(recommendations: list, best: float) -> str:
    """Render recommendations as an ASCII table, wrapping the reasons column."""
    headers = ["#", "Title", "Artist", "Genre / Mood", "Score", "Reasons"]
    rows: List[List[List[str]]] = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        reasons: List[str] = []
        for r in explanation.split("; "):
            reasons.extend(textwrap.wrap(r, 44, subsequent_indent="  "))
        rows.append([
            [str(rank)],
            textwrap.wrap(song["title"], 22),
            textwrap.wrap(song["artist"], 18),
            [song["genre"], song["mood"]],
            [f"{score:.2f}/{best:.2f}"],
            reasons,
        ])
    widths = [
        max([len(headers[c])] + [len(line) for row in rows for line in row[c]])
        for c in range(len(headers))
    ]
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def line(cells: List[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    out = [sep, line(headers), sep.replace("-", "=")]
    for row in rows:
        height = max(len(cell) for cell in row)
        for i in range(height):
            out.append(line([cell[i] if i < len(cell) else "" for cell in row]))
        out.append(sep)
    return "\n".join(out)


def show(name: str, prefs: Dict, songs: list, mode: str, diverse: bool, table: bool,
         weights: dict = None) -> None:
    """Run one profile and print it as a list or a table."""
    strategy = get_strategy(mode, weights)
    recs = recommend_songs(prefs, songs, k=5, mode=strategy, diverse=diverse)
    if not table:
        print_recommendations(name, prefs, recs, strategy.weights)
        return
    tags = [f"mode={strategy.name}"] + (["diverse"] if diverse else [])
    print(f"Profile: {name}  ({', '.join(tags)})")
    print(format_table(recs, strategy.max_score(prefs)))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="VibeFinder music recommender")
    parser.add_argument("--profile", help="run only this profile (substring match)")
    parser.add_argument("--mode", default="genre-first", choices=list(STRATEGIES))
    parser.add_argument("--diverse", action="store_true", help="apply diversity penalty")
    parser.add_argument("--table", action="store_true", help="print an ASCII table")
    parser.add_argument("--compare-modes", action="store_true", help="run every scoring mode")
    parser.add_argument("--list", action="store_true", help="list profiles and modes")
    args = parser.parse_args()

    if args.list:
        print("Profiles:")
        for name in PROFILES:
            print(f"  - {name}")
        print("Scoring modes:")
        for s in STRATEGIES.values():
            print(f"  - {s.name}: {s.description}")
        return

    songs = load_songs("data/songs.csv")
    profiles = PROFILES
    if args.profile:
        profiles = {n: p for n, p in PROFILES.items() if args.profile.lower() in n.lower()}
        if not profiles:
            parser.error(f"no profile matches '{args.profile}' (try --list)")

    modes = list(STRATEGIES) if args.compare_modes else [args.mode]
    for name, prefs in profiles.items():
        for mode in modes:
            label = f"{name} [{mode}]" if args.compare_modes else name
            show(label, prefs, songs, mode, args.diverse, args.table)

    # The original Phase 4 experiment only runs on a plain, full run.
    if args.profile or args.compare_modes or args.diverse or args.table or args.mode != "genre-first":
        return
    print("#" * 64)
    print("EXPERIMENT: Weight Shift (genre 2.0 -> 1.0, energy 1.5 -> 3.0)")
    print("#" * 64)
    for name in ("High-Energy Pop (default)", "Conflicted (energy 0.9 + sad)"):
        show(f"{name} [weight shift]", PROFILES[name], songs, None, False, False,
             weights=EXPERIMENT_WEIGHTS)


if __name__ == "__main__":
    main()
