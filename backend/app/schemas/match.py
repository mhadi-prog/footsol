from datetime import date

from pydantic import BaseModel, ConfigDict


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    statsbomb_match_id: int
    competition: str
    season: str
    match_date: date | None
    home_team: str
    away_team: str
    home_score: int
    away_score: int


class MatchPlayerRating(BaseModel):
    player_id: int
    player_name: str
    rating: float
    breakdown: dict[str, float]


class MatchRatingsOut(BaseModel):
    match: MatchOut
    ratings: list[MatchPlayerRating]


class CompetitionOut(BaseModel):
    competition: str
    season: str
    match_count: int
