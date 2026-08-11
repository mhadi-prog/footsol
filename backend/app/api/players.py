from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.player import (
    DatasetStats,
    PlayerMatchHistoryEntry,
    PlayerOut,
    PlayerSeasonSummary,
    TopPerformance,
)
from app.services import ratings_query

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/search", response_model=list[PlayerOut])
def search_players(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    return ratings_query.search_players(db, q)


@router.get("/meta/top-performances", response_model=list[TopPerformance])
def top_performances(
    limit: int = 8,
    competition: str | None = None,
    season: str | None = None,
    db: Session = Depends(get_db),
):
    return ratings_query.get_top_performances(db, limit, competition, season)


@router.get("/meta/stats", response_model=DatasetStats)
def dataset_stats(competition: str | None = None, season: str | None = None, db: Session = Depends(get_db)):
    return ratings_query.get_dataset_stats(db, competition, season)


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = ratings_query.get_player(db, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/{player_id}/matches", response_model=list[PlayerMatchHistoryEntry])
def get_player_matches(player_id: int, db: Session = Depends(get_db)):
    player = ratings_query.get_player(db, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return ratings_query.get_player_match_history(db, player_id)


@router.get("/{player_id}/summary", response_model=PlayerSeasonSummary)
def get_player_summary(player_id: int, db: Session = Depends(get_db)):
    summary = ratings_query.get_player_season_summary(db, player_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Player not found or has no rated matches")
    return summary
