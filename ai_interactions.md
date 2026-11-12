# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

**What task did you give the agent?**

I asked Claude Code (agent mode) to implement all four optional extensions in one pass: add 5+ advanced song attributes to the dataset and score them (Challenge 1), add switchable scoring modes (Challenge 2), add a diversity penalty for repeated artists/genres (Challenge 3), and add a formatted summary table that includes the reasons (Challenge 4). The work also had to keep the existing tests and the documented Phase 4 outputs valid.

**Prompts used:**

- "Add all optional extensions, please." (the agent already had the full assignment text and the current repo in context)
- The plan the agent followed, effectively these sub-prompts:
  - "Add `popularity` (0–100), `release_decade`, `mood_tags` (several detailed tags like nostalgic/aggressive/euphoric), `instrumentalness`, and `liveness` to every row of `data/songs.csv`, and update `load_songs` to parse them into int/float/list."
  - "Extend `score_song` so each new attribute adds a small, bounded number of points **only when the user profile sets that preference**, and append a reason string for each, so the original profiles' scores don't change."
  - "Wrap the weights in a Strategy object so `main.py` can switch between genre-first, mood-first, and energy-focused modes."
  - "Add a re-ranking step that subtracts points from a song whose artist or genre is already in the top list, and show the penalty as a reason."
  - "Print an ASCII table with rank, title, artist, genre/mood, score, and wrapped reasons, without adding a dependency."

**What did the agent generate or change?**

- `data/songs.csv`: 5 new columns for all 20 songs.
- `src/recommender.py`: new `Song`/`UserProfile` fields with defaults (so the original tests still build `Song` objects without them); five new scoring rules; `max_score()`; `ScoringStrategy` + `STRATEGIES` + `get_strategy()`; `_diversify()` and `rank_songs()`; `recommend_songs` and `Recommender` gained `mode` and `diverse` options.
- `src/main.py`: `argparse` flags (`--profile`, `--mode`, `--compare-modes`, `--diverse`, `--table`, `--list`), a new "Nostalgic Storyteller" profile, and `format_table()`.
- `tests/test_recommender.py`: 8 new tests (type conversion, reasons, energy closeness, advanced features, max score, modes, diversity, table).
- `README.md` / `model_card.md`: documented the extensions with real terminal output.
- Commands run: `python -m src.main` with each flag combination and `python -m pytest` (10 passed).

**What did you verify or fix manually?**

- **Regression check:** diffed the full default output before and after the change. The six original profiles and the weight-shift experiment were byte-for-byte identical, and the only addition was the new profile. That confirmed the "only when requested" design worked.
- **Max-score bug caught earlier:** the old display hard-coded `sum(weights)`, which would have shown `/ 6.90` for profiles that only use four preferences. It was replaced with `max_score()`, which counts only the preferences the profile actually set.
- **Picking a demo that shows the feature:** the diversity penalty didn't change the Deep Intense Rock list at all (it was already all different artists and genres), so I used Chill Lofi instead, where two LoRoom songs were in the top 3.
- **Hand-checked the math:** Focus Flow under diversity = 3.81 − 1.0 (artist) − 0.5 (genre) = 2.31 ✔; Nostalgic Storyteller max = 2.0+1.0+1.5+0.5+0.5+0.6+0.3+0.3+0.2 = 6.9 ✔.
- **Data judgment:** the new attribute values (popularity, decade, tags) are invented, so I checked that they were at least plausible for each fictional song (e.g. the punk song gets high liveness, the classical piece high instrumentalness).

---

## Design Pattern (SF10)

**Which design pattern did you use?**

**Strategy pattern.** Each scoring mode is a `ScoringStrategy` object with the same interface (`score(user_prefs, song)` and `max_score(user_prefs)`), and the ranking code works with any of them.

**How did AI help you brainstorm or implement it?**

I asked how to support "Genre-First," "Mood-First," and "Energy-Focused" modes without copy-pasting the scoring function three times. The AI compared three options:

1. **`if/elif` on a mode string inside `score_song`:** simplest, but every new mode means editing the core function and it grows into a long branch chain.
2. **One subclass per mode overriding `score()`:** a textbook Strategy, but the three modes only differ in their *weights*, so the subclasses would be nearly identical.
3. **A single `ScoringStrategy` class configured with a weights dict, plus a registry (`STRATEGIES`):** still a Strategy (interchangeable objects behind one interface), with no duplicated logic, and a new mode is a single dictionary entry.

We chose option 3. A custom weight dict (like the Phase 4 experiment) is just another strategy, built by `get_strategy(weights=...)`, so the old `weights=` argument kept working. If a future mode needs genuinely different logic (e.g. collaborative filtering), it can subclass `ScoringStrategy` and override `score()` without touching the ranking code.

**How does the pattern appear in your final code?**

- `src/recommender.py`: `class ScoringStrategy` (the strategy), `STRATEGIES` (the registry of concrete modes), and `get_strategy()` (resolves a name, object, or weight dict).
- `rank_songs()` only calls `strategy.score(...)`; it never knows which mode it's using.
- `Recommender.__init__(..., mode=...)` stores a strategy, so the OOP API can switch modes too.
- `src/main.py`: `--mode` and `--compare-modes` pick strategies by name at runtime.
