from __future__ import annotations

from statsbombpy import sb

from app.core.db import SessionLocal
from app.models.match import Match


def _name(value):
    if isinstance(value, dict):
        return value.get("name")
    return value


def main() -> None:
    session = SessionLocal()
    updated = 0
    try:
        competitions = sb.competitions()
        for _, comp_row in competitions.iterrows():
            comp_id = int(comp_row["competition_id"])
            season_id = int(comp_row["season_id"])

            try:
                matches_df = sb.matches(competition_id=comp_id, season_id=season_id)
            except Exception as e:
                print(f"Skipping competition_id={comp_id}, season_id={season_id}: {e}")
                continue

            for _, match_row in matches_df.iterrows():
                statsbomb_match_id = int(match_row["match_id"])
                match = session.query(Match).filter_by(statsbomb_match_id=statsbomb_match_id).one_or_none()
                if match is None or match.stage is not None:
                    continue  # not ingested, or already backfilled

                match.stage = _name(match_row.get("competition_stage"))
                updated += 1

            session.commit()
            print(f"competition_id={comp_id}, season_id={season_id}: backfilled so far, running total {updated}")

    finally:
        session.close()

    print(f"\nDone. Backfilled stage on {updated} matches.")


if __name__ == "__main__":
    main()
