# Episode 05: Why Knowing More Words Makes You Worse at Scrabble (2,005,498 Turns Analyzed)

[![YouTube Video](https://img.shields.io/badge/YouTube-Watch%20Episode%2005-red?logo=youtube)](https://youtu.be/Ro8JRJaJnQo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the simulation engine, multi-agent bot tournament, and empirical aggregated metrics accompanying Episode 05: **"Why Knowing More Words Makes You Worse at Scrabble"**.

---

## 🎬 YouTube Video
- **Watch the full episode:** [https://youtu.be/Ro8JRJaJnQo](https://youtu.be/Ro8JRJaJnQo)
- **Key Paradox:** Casual players think Scrabble is won by walking dictionaries memorizing 8-letter words. By analyzing 2,005,498 competitive turns and pitting 5 bots against each other using the **exact same small household vocabulary**, the math proves the exact opposite: 6-letter words have the lowest efficiency in the game ($5.54\text{ pts/tile}$), while 2-letter parallel hooks and 7-letter Bingos dominate.

---

## 📊 Empirical Findings (`72,773 Games / 2,005,498 Turns`)

Aggregated statistics from competitive match play ([Kaggle Scrabble Player Rating Dataset](https://www.kaggle.com/competitions/scrabble-player-rating/data)):

### 1. The 6-Tile Efficiency Trap (Points Per Tile Placed)
| Tiles Placed | Total Turns | Share | Avg Points | Points / Tile | Strategic Verdict |
|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | `90,656` | `4.8%` | `12.1 pts` | **`12.10`** | Surgical bonus square hook |
| **2** | `345,300` | `18.4%` | `20.2 pts` | **`10.09`** | Parallel 2D overlaps (`QI`, `ZA`, `OX`, `XI`) |
| **3** | `516,630` | `27.6%` | `23.9 pts` | **`7.98`** | Standard cluster play |
| **4** | `396,249` | `21.2%` | `27.2 pts` | **`6.80`** | Intermediate lane play |
| **5** | `219,661` | `11.7%` | `30.8 pts` | **`6.15`** | Declining flexibility |
| **6** | `70,281` | **`3.8%`** | `33.2 pts` | **`5.54`** | **WORST IN GAME (Drains rack, no +50 bonus)** |
| **7** | `234,028` | **`12.5%`** | `76.3 pts` | **`10.90`** | **BINGO (+50 Point Bonus)** |

### 2. Strategic Secrets
- **The 'QI' Monopoly:** `QI` is the #1 most played word in all of competitive Scrabble (`14,221` plays), monopolizing over 50% of all Q usage. `ZA` averages `43.5` points (peaking at `74` points), `XI` peaks at `75` points, and `OX` peaks at `73` points.
- **The Blank Invariant:** `79.5%` of all Blank plays are 7-letter Bingos. The top letters blanks turn into spell **RETINAS** (S 15.5%, E 10.5%, R 7.1%, A 7.0%, T 6.7%, N 6.6%, I 6.5%).
- **The S-Tile Preservation Rule:** Adding an 'S' to an existing word for +1 point drops win rate by 7%. Unless an 'S' adds $\ge +18\text{ points}$, keep it on your rack.
- **The Exchange Miracle:** On the turn immediately following an Exchange, the 50-point Bingo rate surges to `20.2%` (1 in every 5 turns!).

---

## 🤖 5-Bot Tournament Arena

All 5 bots share the **exact same ~3,000-word household vocabulary**, isolating the mathematical rules from dictionary size:

| Bot Archetype | Strategy | Key Mechanism | Win Rate |
|:---|:---|:---|:---:|
| **#1 Long-Word Professor** | Word Length ($\ge 5$ tiles) | Plays big words into open lanes; feeds opponent TW | `18%` |
| **#2 Naive Greedy Scorer** | Immediate Score Maximizer | Burns `S` and Blanks on low-value moves | `34%` |
| **#3 2-Letter Hook Specialist** | Parallel 2D Overlaps | Detonates `ZA, QI, EX, OX, JO` on DL/TL squares | `52%` |
| **#4 Leave & S/Blank Saver** | $\text{Score} + \text{Leave Equity}$ | Holds `S` ($\ge 18$), Blanks ($\ge 35$), keeps `SATIRE` stems | `64%` |
| **#5 Full 4-Rule Tactical AI** | Hooks + Leave + Taxes + Defense | Masterclass integration | **`78%`** |

---

## 🚀 Quickstart

### Run Unit Tests
```bash
pytest simulation/tests
```

### Run Tournament
```bash
python run_tournament.py --games 100
```

---

## 📁 Dataset Source & Reproducibility Note
The aggregated metrics in `data/results.json` were derived from the [Kaggle Scrabble Player Rating Competition](https://www.kaggle.com/competitions/scrabble-player-rating/data) archive of real competitive matches hosted on Woogles.io.

In accordance with Kaggle Data Access & Terms of Service, raw match logs (`games.csv`, `turns.csv`) are not redistributed in this Git repository. To run raw analysis from scratch, download the dataset directly from Kaggle into your local directory.

---

## 📜 License
MIT License.
