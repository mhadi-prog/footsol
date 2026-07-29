from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    statsbomb_player_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    name: Mapped[str] = mapped_column(String(120))
    primary_position: Mapped[str | None] = mapped_column(String(50), nullable=True)
