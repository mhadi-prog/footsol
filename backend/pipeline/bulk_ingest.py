from __future__ import annotations

import argparse
import signal
import time

from statsbombpy import sb

from app.core.db import SessionLocal
from pipeline.ingest import ingest_match


def _timeout_handler(signum, frame):
    raise TimeoutError("Match fetch exceeded 30s, likely a hung connection")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest every available StatsBomb open-data competition/season.")
    parser.add_argument("--max-matches-per-season", type=int, default=None, help="Cap per competition/season, for a faster partial run")
    parser.add_argument("--dry-run", action="store_true", help="List what would be ingested without actually doing it")
    args = parser.parse_args()

    competitions = sb.competitions()
    print(f"Found {len(competitions)} competition/season entries.")

    total_ingested = 0
    total_failed = 0
    session = SessionLocal()

    try:
        for _, comp_row in competitions.iterrows():
            comp_id = int(comp_row["competition_id"])
            season_id = int(comp_row["season_id"])
            label = f"{comp_row['competition_name']} {comp_row['season_name']}"

            try:
                matches_df = sb.matches(competition_id=comp_id, season_id=season_id)
            except Exception as e:
                print(f"  Skipping {label} (competition_id={comp_id}, season_id={season_id}): could not list matches ({e})")
                continue

            if args.max_matches_per_season:
                matches_df = matches_df.head(args.max_matches_per_season)

            print(f"\n{label} (competition_id={comp_id}, season_id={season_id}): {len(matches_df)} matches")

            if args.dry_run:
                continue

            for _, match_row in matches_df.iterrows():
                signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(30)
                try:
                    ingest_match(session, match_row, force=False)
                    total_ingested += 1
                except Exception as e:
                    total_failed += 1
                    print(f"    Failed on match {match_row.get('match_id')}: {e}")
                    session.rollback()
                finally:
                    signal.alarm(0)
                time.sleep(0.2)

    finally:
        session.close()

    print(f"\nDone. Matches processed: {total_ingested}, failed: {total_failed}.")


if __name__ == "__main__":
    main()
