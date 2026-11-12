from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# Tests for the functional API and the optional extensions
# ---------------------------------------------------------------------------

from src.recommender import (
    STRATEGIES,
    load_songs,
    max_score,
    recommend_songs,
    score_song,
)
from src.main import PROFILES, format_table

SONGS = load_songs("data/songs.csv")
POP = PROFILES["High-Energy Pop (default)"]


def test_load_songs_converts_types_and_new_features():
    song = SONGS[0]
    assert len(SONGS) == 20
    assert isinstance(song["energy"], float)
    assert isinstance(song["popularity"], int)
    assert isinstance(song["release_decade"], int)
    assert song["mood_tags"] == ["euphoric", "bright", "summer"]


def test_score_song_returns_score_and_reasons():
    score, reasons = score_song(POP, SONGS[0])  # Sunrise City: pop / happy
    assert score == 4.88
    assert "genre match: pop (+2.0)" in reasons
    assert "mood match: happy (+1.0)" in reasons


def test_energy_rewards_closeness_not_magnitude():
    near = {**SONGS[0], "genre": "x", "mood": "x", "energy": 0.8}
    louder = {**near, "energy": 1.0}
    assert score_song(POP, near)[0] > score_song(POP, louder)[0]


def test_advanced_features_score_only_when_requested():
    storyteller = PROFILES["Nostalgic Storyteller"]
    porch = next(s for s in SONGS if s["title"] == "Dusty Porch Swing")
    _, reasons = score_song(storyteller, porch)
    assert any(r.startswith("from the 1970s") for r in reasons)
    assert any(r.startswith("mood tags: storytelling, warm") for r in reasons)
    _, plain = score_song(POP, porch)
    assert not any("decade" in r or "tags" in r or "1970s" in r for r in plain)


def test_max_score_counts_only_active_preferences():
    assert max_score(POP) == 5.0
    assert round(max_score(PROFILES["Nostalgic Storyteller"]), 2) == 6.9


def test_scoring_modes_change_ranking():
    genre_first = [s["title"] for s, _, _ in recommend_songs(POP, SONGS, k=3)]
    mood_first = [s["title"] for s, _, _ in recommend_songs(POP, SONGS, k=3, mode="mood-first")]
    assert genre_first[1] == "Gym Hero"
    assert mood_first[1] == "Rooftop Lights"
    assert set(STRATEGIES) == {"genre-first", "mood-first", "energy-focused"}


def test_diversity_penalty_breaks_up_repeat_artists():
    lofi = PROFILES["Chill Lofi"]
    plain = recommend_songs(lofi, SONGS, k=5)
    diverse = recommend_songs(lofi, SONGS, k=5, diverse=True)
    top3 = lambda recs: [s["artist"] for s, _, _ in recs[:3]]
    assert top3(plain).count("LoRoom") == 2
    assert top3(diverse).count("LoRoom") == 1
    assert any("diversity: artist already listed" in why for _, _, why in diverse)


def test_table_includes_reasons():
    table = format_table(recommend_songs(POP, SONGS, k=2), 5.0)
    assert "Reasons" in table
    assert "genre match: pop (+2.0)" in table
