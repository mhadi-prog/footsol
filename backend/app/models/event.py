from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    statsbomb_event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)

    team_name: Mapped[str] = mapped_column(String(120))
    event_type: Mapped[str] = mapped_column(String(50), index=True)   # Pass, Duel, Shot, Tackle, ...
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Complete, Won, Lost, ...

    period: Mapped[int] = mapped_column(Integer)
    minute: Mapped[int] = mapped_column(Integer, index=True)
    second: Mapped[int] = mapped_column(Integer)

    location_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_y: Mapped[float | None] = mapped_column(Float, nullable=True)

    under_pressure: Mapped[bool] = mapped_column(Boolean, default=False)

    # Full original StatsBomb event, kept for detail this schema doesn't surface directly
    raw: Mapped[dict] = mapped_column(JSONB)