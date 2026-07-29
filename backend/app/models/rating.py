from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PlayerMatchRating(Base):
    __tablename__ = "player_match_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    position: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating: Mapped[float] = mapped_column(Float)

    # Per-event-type contribution to the final rating, e.g. {"Pass": 0.42, "Duel": -0.1, ...}
    # Lets the API and frontend show *why* a player got their rating, not just the number
    breakdown: Mapped[dict] = mapped_column(JSONB)