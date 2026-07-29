from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.match import Match
from app.models.player import Player
from app.models.rating import PlayerMatchRating
from pipeline.event_weights import compute_event_weights_for_match
from pipeline.win_probability import load_model

BASELINE_RATING = 6.0
MIN_RATING = 0.0
MAX_RATING = 10.0

# High-frequency, low-discrimination event types: capped per player per match so
# repetition alone can't outweigh rarer, more decisive contributions (goals, key
# dribbles, saves). Tune these caps as more matches reveal other volume-driven types.
VOLUME_EVENT_CAPS = {
    "Pass": 0.5,
    "Ball Recovery": 0.4,
    "Clearance": 0.4,
}


def compute_ratings_for_match(session: Session, match: Match, model) -> list[PlayerMatchRating]:
    event_results = compute_event_weights_for_match(session, match, model)

    per_player_weight: dict[int, float] = defaultdict(float)
    per_player_breakdown: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for event, weight, _info in event_results:
        if event.player_id is None:
            continue
        per_player_weight[event.player_id] += weight
        per_player_breakdown[event.player_id][event.event_type] += weight

    ratings = []
    for player_id, breakdown in per_player_breakdown.items():
        capped_breakdown = dict(breakdown)
        for event_type, cap in VOLUME_EVENT_CAPS.items():
            if event_type in capped_breakdown:
                capped_breakdown[event_type] = max(-cap, min(cap, capped_breakdown[event_type]))

        total_weight = sum(capped_breakdown.values())
        rating_value = max(MIN_RATING, min(MAX_RATING, BASELINE_RATING + total_weight))

        rating = PlayerMatchRating(
            match_id=match.id,
            player_id=player_id,
            position=None,  # position weighting deliberately deferred, see event_weights.py
            rating=round(rating_value, 2),
            breakdown={k: round(v, 3) for k, v in capped_breakdown.items()},
        )
        ratings.append(rating)

    return ratings


def persist_ratings(session: Session, match: Match, ratings: list[PlayerMatchRating], force: bool) -> int:
    existing_count = session.query(PlayerMatchRating).filter_by(match_id=match.id).count()
    if existing_count > 0:
        if not force:
            print(f"Match {match.statsbomb_match_id} already has {existing_count} ratings, skipping. Use --force to recompute.")
            return 0
        session.query(PlayerMatchRating).filter_by(match_id=match.id).delete()

    session.add_all(ratings)
    session.commit()
    return len(ratings)


def run_for_match(session: Session, match: Match, model, force: bool) -> None:
    ratings = compute_ratings_for_match(session, match, model)
    inserted = persist_ratings(session, match, ratings, force)
    if inserted:
        print(f"Match {match.statsbomb_match_id} ({match.home_team} vs {match.away_team}): wrote {inserted} player ratings.")


def print_match_ratings(session: Session, match: Match) -> None:
    ratings = (
        session.query(PlayerMatchRating)
        .filter_by(match_id=match.id)
        .order_by(PlayerMatchRating.rating.desc())
        .all()
    )
    print(f"\nRatings, {match.home_team} vs {match.away_team} ({match.home_score}-{match.away_score}):")
    for r in ratings:
        player = session.get(Player, r.player_id)
        top_contributions = sorted(r.breakdown.items(), key=lambda kv: kv[1], reverse=True)[:3]
        breakdown_str = ", ".join(f"{k}: {v:+.2f}" for k, v in top_contributions)
        print(f"  {r.rating:>4.1f}  {player.name:<28} ({breakdown_str})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute player match ratings.")
    parser.add_argument("--match-id", type=int, help="StatsBomb match_id. If omitted, runs all matches.")
    parser.add_argument("--force", action="store_true", help="Recompute even if ratings already exist")
    parser.add_argument("--show", action="store_true", help="Print the resulting ratings after computing")
    args = parser.parse_args()

    model = load_model()
    session = SessionLocal()
    try:
        if args.match_id is not None:
            match = session.query(Match).filter_by(statsbomb_match_id=args.match_id).one_or_none()
            if match is None:
                print(f"Match {args.match_id} not found. Ingest it first.")
                return
            matches = [match]
        else:
            matches = session.query(Match).all()

        for match in matches:
            run_for_match(session, match, model, args.force)

        if args.show:
            target = matches[0] if args.match_id else matches[-1]
            print_match_ratings(session, target)
    finally:
        session.close()


if __name__ == "__main__":
    main()
