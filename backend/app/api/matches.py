from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.match import CompetitionOut, MatchOut, MatchRatingsOut
from app.services import ratings_query

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/competitions", response_model=list[CompetitionOut])
def list_competitions(db: Session = Depends(get_db)):
    return ratings_query.get_competitions(db)


@router.get("", response_model=list[MatchOut])
def list_matches(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return ratings_query.list_matches(db, limit=limit, offset=offset)


@router.get("/{statsbomb_match_id}/ratings", response_model=MatchRatingsOut)
def get_match_ratings(statsbomb_match_id: int, db: Session = Depends(get_db)):
    match = ratings_query.get_match_by_statsbomb_id(db, statsbomb_match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    ratings = ratings_query.get_match_ratings(db, match)
    return {"match": match, "ratings": ratings}
