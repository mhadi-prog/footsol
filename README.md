# footsol

A context-weighted football player rating engine, built on StatsBomb's free
open event data. Instead of a flat "add up the good stuff a player did,"
every action is weighted by how much it actually mattered in the moment it
happened — a last-gasp tackle in a tied game counts for more than a routine
one at 4-0, and a goal in a World Cup Final counts for more than the same
goal in a friendly.

Built as a FastAPI + React learning project, and a genuine attempt at a
defensible alternative to black-box match ratings like Sofascore/Fotmob.

## What it actually does

1. **Ingests** deep, event-level football data (passes, duels, tackles,
   pressures, shots with expected goals) from StatsBomb's free open dataset —
   currently spanning World Cups, Euros, Copa América, AFCON, multiple
   Bundesliga and La Liga seasons, and several major women's competitions.
2. **Trains a win-probability model** on every ingested match's actual
   outcome, learning `P(win/draw/loss | score difference, minutes remaining)`.
3. **Weights every event** by combining a base value (how good the action
   was in isolation, with shots scored against their own xG) with a
   *leverage multiplier* — how much a hypothetical goal right then would
   have swung that team's win probability. This is what makes a late,
   close-game action worth more than an early or blowout one.
4. **Aggregates into a per-match rating** per player, then further into a
   **context-weighted season summary** that additionally accounts for
   competition tier and tournament stage (a World Cup Final performance
   counts for more toward a player's overall picture than an equally good
   group-stage one) — without changing what any single match's rating means.
5. **Serves it all** through a FastAPI backend and a React dashboard for
   searching players, browsing match histories, and filtering standout
   performances by competition.

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL, scikit-learn
- **Data pipeline**: `statsbombpy` for ingestion, pandas for processing
- **Frontend**: React (Vite), react-router
- **Infra**: Docker Compose (Postgres)

## Architecture

StatsBomb Open Data
|
v
Ingestion pipeline -> Postgres (raw events, matches, players)
|
v
Win-probability model (scikit-learn, trained on real match outcomes)
|
v
Event weighting (base value x leverage) -> per-match player ratings
|
v
FastAPI backend (REST) -> React dashboard
# 1. Start Postgres
cd backend
docker compose up -d

# 2. Install backend dependencies
pip install -r requirements.txt --break-system-packages
cp .env.example .env

# 3. Run migrations
alembic upgrade head

# 4. Ingest data (see pipeline/ commands below)
python -m pipeline.bulk_ingest

# 5. Train the win-probability model
python -m pipeline.win_probability --train

# 6. Compute player ratings
python -m pipeline.rating_engine

# 7. Start the API
uvicorn app.main:app --reload
```

```bash
# 8. In a separate terminal, start the frontend
Full reasoning and design decisions (including a few dead ends worth
learning from) are documented in [`docs/methodology.md`](docs/methodology.md).
The short version:

- **Base event value**: what an action was worth on its own — a completed
  dribble beats a routine pass, a won tackle beats a lost one, shots are
  scored against their own StatsBomb xG so scoring from a low-probability
  chance is worth more than a tap-in.
- **Leverage**: derived from the trained win-probability model — for every
  event, how much a hypothetical goal right then would swing that team's
  win probability. Late and close beats early or one-sided.
- **Volume controls**: high-frequency, low-discrimination event types
  (routine passes, ball recoveries, clearances) are capped per player per
  match, so racking up a lot of routine touches can't outscore a genuinely
  decisive contribution like a match-winning goal.
- **Context weighting** (season/aggregate level only, never the per-match
  number itself): competition tier and tournament stage scale how much a
  performance counts toward a player's overall picture, so a Final
  performance means more than an equivalent group-stage one.

## Known limitations

- **Position weighting is not yet implemented.** A defensive action from a
  striker isn't valued more highly than the same action from a defender,
  despite being rarer given their role. This is the single biggest planned
  improvement.
- **Volume caps are a blunt instrument.** They stop any one event category
  from dominating a rating, but a player who's heavily involved across
  *several* capped categories simultaneously can still rate unrealistically
  highly. Two attempts at a smooth diminishing-returns curve (sqrt, asinh)
  both failed to fix this at the actual scale of the data — documented in
  `docs/methodology.md` as a worked example of why.
- **Competition and stage weights are hand-set judgment calls**
  (`backend/app/services/context_weights.py`), not derived from data. Feel
  free to disagree with specific numbers and adjust the table.
- **Data is limited to StatsBomb's free open tier** — deep and high-quality,
  but not every league, season, or match is covered.

## Data source

All match and event data comes from [StatsBomb's Open Data](https://github.com/statsbomb/open-data),
used under their open data license. Not affiliated with or endorsed by
StatsBomb.

