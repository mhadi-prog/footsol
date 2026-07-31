from pydantic import BaseModel, ConfigDict


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    statsbomb_player_id: int
    name: str
    primary_position: str | None


class PlayerMatchRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    rating: float
    breakdown: dict[str, float]


class PlayerMatchHistoryEntry(BaseModel):
    statsbomb_match_id: int
    competition: str
    season: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    rating: float
    breakdown: dict[str, float]
    goals: int
    assists: int


class PlayerSeasonSummary(BaseModel):
    player: PlayerOut
    matches_played: int
    average_rating: float
    highest_rating: float
    lowest_rating: float


class TopPerformance(BaseModel):
    player_id: int
    player_name: str
    rating: float
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    competition: str
    goals: int
    assists: int


class DatasetStats(BaseModel):
    matches: int
    players: int
    ratings: int
    competitions: int
