from __future__ import annotations

import argparse
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.event import Event
from app.models.match import Match
from app.models.player import Player
from pipeline.win_probability import _goal_events_for_match, load_model, predict_win_probability

# How strongly leverage amplifies the base event value.
# weight = base_value * (1 + LEVERAGE_SCALE * leverage)
# leverage is a probability delta in [0, ~0.6] in practice, so this keeps
# high-leverage events at roughly 2-3x their base value, never zeroing one out.
LEVERAGE_SCALE = 2.5

GOAL_BASE_VALUE = 0.8
XG_BONUS_SCALE = 0.6      # rewards scoring from a low-xG chance
XG_MISS_PENALTY_SCALE = 0.3  # penalizes missing a high-xG chance

# (event_type, outcome) -> base value. outcome is None for events where
# StatsBomb only records an outcome on failure (e.g. a completed pass has
# no pass_outcome field at all, so it lands here as None = success).
# NOTE: this table is a starting point, not exhaustive - run the inspection
# query below and extend it once you see the real outcome strings in your data.
BASE_EVENT_VALUES: dict[tuple[str, str | None], float] = {
    ("Pass", None): 0.008,
    ("Pass", "Incomplete"): -0.05,
    ("Pass", "Out"): -0.05,
    ("Pass", "Pass Offside"): -0.05,
    ("Pass", "Unknown"): -0.02,

    ("Dribble", "Complete"): 0.15,
    ("Dribble", "Incomplete"): -0.10,

    ("Duel", "Won"): 0.10,
    ("Duel", "Success In Play"): 0.10,
    ("Duel", "Success Out"): 0.05,
    ("Duel", "Lost In Play"): -0.10,
    ("Duel", "Lost Out"): -0.05,

    ("Interception", "Won"): 0.15,
    ("Interception", None): 0.10,

    ("Ball Recovery", None): 0.08,
    ("Clearance", None): 0.05,
    ("Block", None): 0.12,

    ("Foul Committed", None): -0.10,
    ("Foul Committed", "Penalty"): -0.60,

    ("Dispossessed", None): -0.08,
    ("Miscontrol", None): -0.08,
    ("Goal Keeper", None): 0.01,
    ("Goal Keeper", "Success"): 0.05,
    ("Goal Keeper", "Claim"): 0.15,
    ("Goal Keeper", "Collected Twice"): 0.12,
    ("Goal Keeper", "Saved Twice"): 0.25,
    ("Goal Keeper", "Punched out"): 0.10,
    ("Goal Keeper", "Touched Out"): 0.15,
    ("Goal Keeper", "In Play Safe"): 0.08,
    ("Goal Keeper", "In Play Danger"): -0.05,
    ("Goal Keeper", "Touched In"): -0.05,
    ("Goal Keeper", "No Touch"): 0.0,
    ("Goal Keeper", "Fail"): -0.15,
    ("Goal Keeper", "Won"): 0.10,
    ("Goal Keeper", "Lost"): -0.10,
    ("Goal Keeper", "Success In Play"): 0.10,
    ("Goal Keeper", "Success Out"): 0.05,
    ("Goal Keeper", "Lost In Play"): -0.10,
    ("Goal Keeper", "Lost Out"): -0.05,
}


def _shot_base_value(event: Event) -> float:
    xg = float(event.raw.get("shot_statsbomb_xg", 0.1))
    if event.outcome == "Goal":
        return GOAL_BASE_VALUE + (1 - xg) * XG_BONUS_SCALE
    return -xg * XG_MISS_PENALTY_SCALE


def base_event_value(event: Event) -> float:
    if event.event_type == "Shot":
        return _shot_base_value(event)

    key = (event.event_type, event.outcome)
    if key in BASE_EVENT_VALUES:
        return BASE_EVENT_VALUES[key]

    # Fall back to the "default/success" entry for this event type, if any
    fallback = BASE_EVENT_VALUES.get((event.event_type, None))
    return fallback if fallback is not None else 0.0


@lru_cache(maxsize=None)
def _cached_leverage(model_id: int, model, score_diff: int, minute: int) -> float:
    # model_id exists only to make the cache key explicit/readable; the model
    # object itself is what actually gets used.
    current = predict_win_probability(model, score_diff, minute)
    next_goal = predict_win_probability(model, score_diff + 1, minute)
    return max(0.0, next_goal["win"] - current["win"])


def compute_leverage(model, score_diff: int, minute: int) -> float:
    return _cached_leverage(id(model), model, score_diff, minute)


def compute_event_weights_for_match(
    session: Session, match: Match, model
) -> list[tuple[Event, float, dict]]:
    goals = _goal_events_for_match(session, match.id)

    events = (
        session.query(Event)
        .filter(Event.match_id == match.id)
        .order_by(Event.period, Event.minute, Event.second)
        .all()
    )

    results = []
    for event in events:
        base_value = base_event_value(event)
        if base_value == 0.0:
            continue  # event type not yet valued - skip rather than pollute output with zeros

        opponent = match.away_team if event.team_name == match.home_team else match.home_team
        team_goals = sum(1 for team, m in goals if team == event.team_name and m < event.minute)
        opp_goals = sum(1 for team, m in goals if team == opponent and m < event.minute)
        score_diff = team_goals - opp_goals

        leverage = compute_leverage(model, score_diff, event.minute)
        weight = base_value * (1 + LEVERAGE_SCALE * leverage)

        results.append((event, weight, {
            "base_value": base_value,
            "leverage": leverage,
            "score_diff": score_diff,
        }))

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute context-weighted event values for a match.")
    parser.add_argument("--match-id", type=int, required=True, help="StatsBomb match_id, not the internal DB id")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    model = load_model()
    session = SessionLocal()
    try:
        match = session.query(Match).filter_by(statsbomb_match_id=args.match_id).one_or_none()
        if match is None:
            print(f"Match {args.match_id} not found in the database. Ingest it first.")
            return

        results = compute_event_weights_for_match(session, match, model)
        results.sort(key=lambda r: r[1], reverse=True)

        print(f"Top {args.top} highest-weighted events, {match.home_team} vs {match.away_team}:")
        for event, weight, info in results[: args.top]:
            player = session.get(Player, event.player_id) if event.player_id else None
            player_name = player.name if player else "Unknown"
            print(
                f"  {weight:+.3f}  min {event.minute:>2}  {player_name:<25} "
                f"{event.event_type:<12} {event.outcome or 'Success':<12} "
                f"(base={info['base_value']:+.2f}, leverage={info['leverage']:.2f}, "
                f"score_diff={info['score_diff']:+d})"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
