from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    statsbomb_match_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    competition: Mapped[str] = mapped_column(String(120))
    season: Mapped[str] = mapped_column(String(20))
    match_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    home_team: Mapped[str] = mapped_column(String(120))
    away_team: Mapped[str] = mapped_column(String(120))
    home_score: Mapped[int] = mapped_column(Integer)
    away_score: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(80), nullable=True)