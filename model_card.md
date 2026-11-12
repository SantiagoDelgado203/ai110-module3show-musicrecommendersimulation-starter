# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

**Goal / task:** VibeFinder suggests the 5 songs from a small catalog that best fit one listener's stated taste. It predicts "how well does this song match what you said you like?" and turns that into a ranked list with reasons.

- It generates a top-5 list, and each song has a score and a short explanation.
- It assumes the user can describe their taste with one favorite genre, one favorite mood, a target energy level (0–1), and whether they like acoustic sound.
- It is built for **classroom exploration**, to learn how recommenders turn data into rankings.

**Intended use:** learning, demos, and experimenting with how weights change rankings.

**Not intended for:** real users on a real music app, any decision that matters (ads, payouts to artists, playlist placement), or judging what music is "good." It knows nothing about a user's history, lyrics, language, or culture, and its song data is hand-made.

---

## 3. How the Model Works

Think of it as a judge holding a scorecard for every song:

- **Same genre as your favorite?** +2 points.
- **Same mood as your favorite?** +1 point.
- **Energy close to what you want?** Up to +1.5 points. A song at exactly your energy gets all 1.5, and it loses points the further away it is. A song isn't rewarded for being louder, only for being *closer*.
- **Acoustic sound matches your taste?** Up to +0.5. If you like acoustic music, more acoustic songs get more; if not, more produced/electronic songs get more.

The best possible score is 5.0. After every song is scored, they are sorted from highest to lowest (ties go to the song with the closer energy) and the top 5 are shown. Each point awarded is printed as a reason, like "genre match: pop (+2.0)."

**Changes from the starter:** the starter returned an empty list. I implemented the CSV loader, the scoring rule, the ranking, the explanations, and the `Recommender` class, and I added the acoustic-preference bonus and a way to pass in different weights for experiments.

---

## 4. Data

- **20 songs** in `data/songs.csv`. The starter had 10, and I added 10 more.
- **Features per song:** genre, mood, energy, tempo (BPM), valence (positivity), danceability, acousticness. Only genre, mood, energy, and acousticness are used for scoring.
- **17 genres** (pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, metal, classical, country, r&b, edm, reggae, folk, blues, punk) and **16 moods** (happy, chill, intense, relaxed, moody, focused, confident, angry, peaceful, nostalgic, romantic, euphoric, uplifting, sad, melancholy, rebellious).
- **What I added:** genres and moods the starter was missing, like metal/angry, classical/peaceful, folk/sad, and edm/euphoric, so very different users could be tested.
- **What's missing:** most genres have only **one** song, so lofi (3) and pop (2) are over-represented compared with everything else. There is no non-English music, no lyrics, no release year, no popularity, and the numbers are my own estimates, not measured audio features.

---

## 5. Strengths

- **Clear, single-genre tastes work well.** The "Chill Lofi" profile got all three lofi songs, then ambient, then quiet jazz. That's exactly what I'd put on a study playlist.
- **The energy rule captures "vibe."** Even with no genre match, the leftover picks have the right intensity. Rock fans get loud songs and lofi fans get quiet ones.
- **Every result is explainable.** Because each point comes with a reason, it's easy to see *why* a song ranked where it did and to spot when the logic is wrong.
- **The acoustic bonus separates look-alikes.** It pushes acoustic jazz above electronic songs for the lofi fan, and does the reverse for the rock fan.

---

## 6. Limitations and Bias

**Main weakness I found: the genre bonus creates a filter bubble, and it hurts users of rare genres most.** A genre match is worth +2.0, which is more than a perfect energy match (+1.5) and a mood match (+1.0) can make up for on their own. In the "Conflicted" profile (folk, sad, but energy 0.9), the one folk song won with an energy of 0.26, the opposite of what the user asked for, simply because the label matched. Because 15 of the 17 genres have only one song, a fan of rock, metal, jazz, or folk gets one real match and then four "filler" songs chosen only for loudness. The same few high-energy songs (*Paper Hearts Riot*, *Gym Hero*, *Storm Runner*) keep appearing for very different people. Meanwhile lofi fans, who have three songs to choose from, get a much better list. So the system quietly favors users whose taste happens to be well stocked in the catalog.

Other limitations:

- **Exact text matching:** "indie pop" gets zero genre credit for a "pop" fan, and "relaxed" gets zero mood credit for "chill."
- **Energy gap is uneven:** a user who wants energy 0.5 can never lose more than 0.75 energy points, while a user at 0.1 or 0.9 can lose well over 1 point. Extreme-energy users get bigger score swings than middle users.
- **Unused features:** tempo, valence, and danceability are ignored, so a sad song and a happy song with the same energy look identical except for the mood label.
- **Silent failure:** a genre that isn't in the catalog (like "k-pop") just never matches, and the user isn't told.

---

## 7. Evaluation

I ran six profiles through `python -m src.main` and read the top 5 for each (full output is in the README under "Experiments You Tried"):

| Profile | Top pick | Felt right? |
| --- | --- | --- |
| High-Energy Pop (pop, happy, 0.8, produced) | Sunrise City | Yes |
| Chill Lofi (lofi, chill, 0.35, acoustic) | Library Rain | Yes, the best list overall |
| Deep Intense Rock (rock, intense, 0.9, produced) | Storm Runner | #1 yes, #2–5 are filler |
| Conflicted (folk, sad, **0.9**, acoustic) | Empty Train Platform | No, energy ignored |
| Unknown Genre (k-pop, happy, 0.7, produced) | Rooftop Lights | Okay, but a silent fallback |
| Middle-of-the-Road (jazz, romantic, 0.5, acoustic) | Coffee Shop Stories | Debatable |

**Comparing pairs of profiles:**

- **Pop vs. Lofi:** the pop list is all songs above 0.75 energy and mostly electronic, while the lofi list is all below 0.45 energy and mostly acoustic. That makes sense: the two profiles disagree on energy *and* acoustic taste, so they share zero songs.
- **Pop vs. Rock:** both lists include *Gym Hero* and *Paper Hearts Riot*. Both users want loud, produced music, so after the genre match the energy rule pulls in the same loud tracks. *Gym Hero* is #2 for pop because of the genre points and #2 for rock because of the "intense" mood, so it gets in for two different reasons.
- **Rock vs. Conflicted:** both ask for energy around 0.9, and three of the same loud songs (Storm Runner, Gym Hero, Paper Hearts Riot) appear in both lists. The difference is #1: rock gets a true match, while the conflicted user gets a quiet folk song because the genre and mood labels outvoted energy. This shows the labels are worth more than the "feel" of the music.
- **Lofi vs. Middle-of-the-Road:** both like acoustic music, so *Coffee Shop Stories* and *Focus Flow* show up in both. The lofi list is much more confident (scores near 5) because three songs match its genre, while the jazz list drops off fast after #1 because there is only one jazz song.
- **Pop vs. Unknown Genre (k-pop):** the same two happy songs top both lists, but in a different order. Without any genre points, *Rooftop Lights* (energy 0.76) edges past *Sunrise City* (0.82) because it's closer to the k-pop fan's 0.7 target.

**Why does "Gym Hero" keep showing up for someone who just wants happy pop?** The system gives a big +2 for "it's pop," and Gym Hero is pop. It's also loud and electronic, which this listener said they like. The only thing wrong with it is the mood ("intense" instead of "happy"), and a mood miss only costs 1 point. So on paper it's the second-best song, even though a person would say a gym anthem isn't really "happy pop."

**Experiment, Weight Shift (genre 2.0 → 1.0, energy 1.5 → 3.0):** for the pop fan, *Rooftop Lights* moved up to #2 and *Gym Hero* dropped to #3. That's **more accurate** to me. For the conflicted user the folk song barely held on to #1 (3.53 vs. 3.02). The ranking became energy-driven instead of label-driven, which is just **different**, not better: now loud songs crowd out everything for any high-energy user. I kept the original weights as the default.

**What surprised me:** how often the bottom of the top 5 was the same few songs, and how convincing the results looked even when they were clearly wrong, just because each one came with a list of reasons.

I also ran the unit tests (`pytest`), which check that the OOP `Recommender` ranks the pop/happy song first and returns a non-empty explanation. Both pass.

---

## 8. Future Work

1. **Partial matches:** give some credit for related genres and moods ("indie pop" ≈ "pop", "relaxed" ≈ "chill") using a small similarity table instead of exact text.
2. **Diversity rule:** penalize a song if its artist or genre is already in the top 5, so filler slots show variety instead of the same loud songs every time.
3. **Use more features and multiple favorites:** add valence and tempo to the score, let users list several genres/moods, and tell the user when their genre isn't in the catalog.

---

## 9. Personal Reflection

**Biggest learning moment:** running the "Conflicted" profile. I expected the energy rule to matter, but the folk song with the wrong energy still won by over 2 points. That's when I understood that weights aren't neutral settings. They decide whose idea of a "vibe" wins, and I had picked them on gut feeling.

**How AI tools helped, and when I double-checked:** the AI assistant was fast at writing the CSV loader, the scoring function, and the formatting, and at suggesting adversarial profiles I wouldn't have thought of (like a genre that doesn't exist). I still had to check its work. For example, the experiment output first said "/ 5.00" even though the experiment weights add up to 5.5, and the README setup instructions had an unclosed code block. I also checked the rankings by hand against my own sense of the songs, since the code can run perfectly and still give a list that doesn't feel right.

**What surprised me:** how much a few lines of arithmetic *feel* like a real recommendation. Printing "genre match (+2.0)" next to a song makes it look thoughtful even when the pick is questionable. That made me realize the explanation and presentation are a big part of why people trust apps like Spotify.

**What I'd try next:** add collaborative filtering with a few fake users' play histories to see how "people like you also liked" changes the results, and add a diversity penalty so the top 5 isn't dominated by the same high-energy songs.
