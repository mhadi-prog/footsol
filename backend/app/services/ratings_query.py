from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.match import Match
from app.models.player import Player
from app.models.rating import PlayerMatchRating


def get_player(session: Session, player_id: int) -> Player | None:
    return session.get(Player, player_id)


def search_players(session: Session, query: str, limit: int = 20) -> list[Player]:
    return (
        session.query(Player)
        .filter(Player.name.ilike(f"%{query}%"))
        .order_by(Player.name)
        .limit(limit)
        .all()
    )


def _goals_by_player_match(session: Session, match_ids: list[int]) -> dict[tuple[int, int], int]:
    if not match_ids:
        return {}
    rows = (
        session.query(Event.player_id, Event.match_id, func.count(Event.id))
        .filter(
            Event.match_id.in_(match_ids),
            Event.event_type == "Shot",
            Event.outcome == "Goal",
            Event.player_id.isnot(None),
        )
        .group_by(Event.player_id, Event.match_id)
        .all()
    )
    return {(pid, mid): count for pid, mid, count in rows}


def _assists_by_player_match(session: Session, match_ids: list[int]) -> dict[tuple[int, int], int]:
    if not match_ids:
        return {}
    rows = (
        session.query(Event.player_id, Event.match_id, func.count(Event.id))
        .filter(
            Event.match_id.in_(match_ids),
            Event.event_type == "Pass",
            Event.player_id.isnot(None),
            Event.raw["pass_goal_assist"].astext == "true",
        )
        .group_by(Event.player_id, Event.match_id)
        .all()
    )
    return {(pid, mid): count for pid, mid, count in rows}


def get_player_match_history(session: Session, player_id: int) -> list[dict]:
    rows = (
        session.query(PlayerMatchRating, Match)
        .join(Match, PlayerMatchRating.match_id == Match.id)
        .filter(PlayerMatchRating.player_id == player_id)
        .order_by(Match.match_date.desc().nullslast())
        .all()
    )

    match_ids = [match.id for _, match in rows]
    goals_map = _goals_by_player_match(session, match_ids)
    assists_map = _assists_by_player_match(session, match_ids)

    return [
        {
            "statsbomb_match_id": match.statsbomb_match_id,
            "competition": match.competition,
            "season": match.season,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "rating": rating.rating,
            "breakdown": rating.breakdown,
            "goals": goals_map.get((player_id, match.id), 0),
            "assists": assists_map.get((player_id, match.id), 0),
        }
        for rating, match in rows
    ]


def get_player_season_summary(session: Session, player_id: int) -> dict | None:
    player = get_player(session, player_id)
    if player is None:
        return None

    stats = (
        session.query(
            func.count(PlayerMatchRating.id),
            func.avg(PlayerMatchRating.rating),
            func.max(PlayerMatchRating.rating),
            func.min(PlayerMatchRating.rating),
        )
        .filter(PlayerMatchRating.player_id == player_id)
        .one()
    )
    matches_played, avg_rating, max_rating, min_rating = stats

    if matches_played == 0:
        return None

    return {
        "player": player,
        "matches_played": matches_played,
        "average_rating": round(avg_rating, 2),
        "highest_rating": max_rating,
        "lowest_rating": min_rating,
    }


def get_match_by_statsbomb_id(session: Session, statsbomb_match_id: int) -> Match | None:
    return session.query(Match).filter_by(statsbomb_match_id=statsbomb_match_id).one_or_none()


def get_match_ratings(session: Session, match: Match) -> list[dict]:
    rows = (
        session.query(PlayerMatchRating, Player)
        .join(Player, PlayerMatchRating.player_id == Player.id)
        .filter(PlayerMatchRating.match_id == match.id)
        .order_by(PlayerMatchRating.rating.desc())
        .all()
    )

    goals_map = _goals_by_player_match(session, [match.id])
    assists_map = _assists_by_player_match(session, [match.id])

    return [
        {
            "player_id": player.id,
            "player_name": player.name,
            "rating": rating.rating,
            "breakdown": rating.breakdown,
            "goals": goals_map.get((player.id, match.id), 0),
            "assists": assists_map.get((player.id, match.id), 0),
        }
        for rating, player in rows
    ]


def list_matches(session: Session, limit: int = 50, offset: int = 0) -> list[Match]:
    return (
        session.query(Match)
        .order_by(Match.match_date.desc().nullslast())
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_top_performances(session: Session, limit: int = 8) -> list[dict]:
    rows = (
        session.query(PlayerMatchRating, Player, Match)
        .join(Player, PlayerMatchRating.player_id == Player.id)
        .join(Match, PlayerMatchRating.match_id == Match.id)
        .order_by(PlayerMatchRating.rating.desc())
        .limit(limit)
        .all()
    )

    match_ids = [match.id for _, _, match in rows]
    goals_map = _goals_by_player_match(session, match_ids)
    assists_map = _assists_by_player_match(session, match_ids)

    return [
        {
            "player_id": player.id,
            "player_name": player.name,
            "rating": rating.rating,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "competition": match.competition,
            "goals": goals_map.get((player.id, match.id), 0),
            "assists": assists_map.get((player.id, match.id), 0),
        }
        for rating, player, match in rows
    ]


def get_dataset_stats(session: Session) -> dict:
    return {
        "matches": session.query(func.count(Match.id)).scalar(),
        "players": session.query(func.count(Player.id)).scalar(),
        "ratings": session.query(func.count(PlayerMatchRating.id)).scalar(),
        "competitions": session.query(func.count(func.distinct(Match.competition))).scalar(),
    }
