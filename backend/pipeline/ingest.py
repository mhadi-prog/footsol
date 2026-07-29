from __future__ import annotations

import argparse
import sys
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session
from statsbombpy import sb

from app.core.db import SessionLocal
from app.models.event import Event
from app.models.match import Match
from app.models.player import Player


def _name(value):
    """StatsBomb fields are sometimes {'id':.., 'name':..} dicts, sometimes plain strings."""
    if isinstance(value, dict):
        return value.get("name")
    return value


def list_competitions() -> None:
    comps = sb.competitions()
    print(comps[["competition_id", "season_id", "competition_name", "season_name"]].to_string(index=False))


def get_or_create_match(session: Session, match_row: pd.Series) -> Match:
    statsbomb_match_id = int(match_row["match_id"])
    match = session.query(Match).filter_by(statsbomb_match_id=statsbomb_match_id).one_or_none()
    if match:
        return match

    match_date = None
    raw_date = match_row.get("match_date")
    if raw_date:
        try:
            match_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
        except ValueError:
            match_date = None

    match = Match(
        statsbomb_match_id=statsbomb_match_id,
        competition=_name(match_row.get("competition")),
        season=_name(match_row.get("season")),
        match_date=match_date,
        home_team=_name(match_row.get("home_team")),
        away_team=_name(match_row.get("away_team")),
        home_score=int(match_row.get("home_score", 0)),
        away_score=int(match_row.get("away_score", 0)),
    )
    session.add(match)
    session.flush()
    return match


def get_or_create_player(session: Session, statsbomb_player_id: int, name: str, position: str | None) -> Player:
    player = session.query(Player).filter_by(statsbomb_player_id=statsbomb_player_id).one_or_none()
    if player:
        return player

    player = Player(
        statsbomb_player_id=statsbomb_player_id,
        name=name,
        primary_position=position,
    )
    session.add(player)
    session.flush()
    return player


def _extract_outcome(row: pd.Series) -> str | None:
    """Different event types store outcome under different column names
    (pass_outcome, shot_outcome, duel_outcome, dribble_outcome, ...).
    Return whichever is present and non-null for this row."""
    for col in row.index:
        if col.endswith("_outcome") and pd.notna(row[col]):
            return _name(row[col])
    return None


def ingest_match(session: Session, match_row: pd.Series, force: bool = False) -> None:
    statsbomb_match_id = int(match_row["match_id"])

    existing = session.query(Match).filter_by(statsbomb_match_id=statsbomb_match_id).one_or_none()
    if existing and not force:
        event_count = session.query(Event).filter_by(match_id=existing.id).count()
        if event_count > 0:
            print(f"Match {statsbomb_match_id} already ingested ({event_count} events), skipping. Use --force to re-ingest.")
            return

    match = get_or_create_match(session, match_row)

    if force:
        session.query(Event).filter_by(match_id=match.id).delete()

    print(f"Fetching events for match {statsbomb_match_id} ({match.home_team} vs {match.away_team})...")
    events_df = sb.events(match_id=statsbomb_match_id, split=False, flatten_attrs=True)

    inserted = 0
    for _, row in events_df.iterrows():
        player_id = None
        raw_player_id = row.get("player_id")
        if pd.notna(raw_player_id):
            player = get_or_create_player(
                session,
                statsbomb_player_id=int(raw_player_id),
                name=_name(row.get("player")) or "Unknown",
                position=_name(row.get("position")),
            )
            player_id = player.id

        location = row.get("location")
        location_x, location_y = (None, None)
        if isinstance(location, list) and len(location) == 2:
            location_x, location_y = location[0], location[1]

        under_pressure_raw = row.get("under_pressure")
        under_pressure = bool(under_pressure_raw) if pd.notna(under_pressure_raw) else False

        event = Event(
            statsbomb_event_id=str(row["id"]),
            match_id=match.id,
            player_id=player_id,
            team_name=_name(row.get("team")) or "Unknown",
            event_type=_name(row.get("type")) or "Unknown",
            outcome=_extract_outcome(row),
            period=int(row.get("period", 0)),
            minute=int(row.get("minute", 0)),
            second=int(row.get("second", 0)),
            location_x=location_x,
            location_y=location_y,
            under_pressure=under_pressure,
            raw=row.dropna().to_dict(),
        )
        session.add(event)
        inserted += 1

    session.commit()
    print(f"Inserted {inserted} events for match {statsbomb_match_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest StatsBomb open data into Postgres.")
    parser.add_argument("--list-competitions", action="store_true")
    parser.add_argument("--competition-id", type=int)
    parser.add_argument("--season-id", type=int)
    parser.add_argument("--match-id", type=int, help="Ingest a single match only")
    parser.add_argument("--limit", type=int, default=1, help="Max matches to ingest when not using --match-id")
    parser.add_argument("--force", action="store_true", help="Re-ingest even if the match already exists")
    args = parser.parse_args()

    if args.list_competitions:
        list_competitions()
        return

    if args.competition_id is None or args.season_id is None:
        print("Provide --competition-id and --season-id (run --list-competitions to find them).")
        sys.exit(1)

    matches_df = sb.matches(competition_id=args.competition_id, season_id=args.season_id)

    if args.match_id is not None:
        matches_df = matches_df[matches_df["match_id"] == args.match_id]
        if matches_df.empty:
            print(f"Match {args.match_id} not found in that competition/season.")
            sys.exit(1)
    else:
        matches_df = matches_df.head(args.limit)

    session = SessionLocal()
    try:
        for _, match_row in matches_df.iterrows():
            ingest_match(session, match_row, force=args.force)
    finally:
        session.close()


if __name__ == "__main__":
    main()
