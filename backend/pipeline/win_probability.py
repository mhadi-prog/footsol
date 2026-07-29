from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.event import Event
from app.models.match import Match

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "win_probability.joblib"

# 'Own Goal For' is attributed by StatsBomb to the team that BENEFITS from the
# own goal, so its team_name can be treated as the scoring team directly -
# no need to flip it relative to the conceding team.
GOAL_EVENT_TYPES = {"Shot", "Own Goal For"}


def _goal_events_for_match(session: Session, match_id: int) -> list[tuple[str, int]]:
    """Return [(scoring_team, minute), ...] for every goal in a match, chronological.
    Excludes period 5 (penalty shootouts), since those aren't part of the
    0-90 minute win-probability window and use a separate scoring context."""
    events = (
        session.query(Event)
        .filter(
            Event.match_id == match_id,
            Event.event_type.in_(GOAL_EVENT_TYPES),
            Event.period != 5,
        )
        .order_by(Event.period, Event.minute, Event.second)
        .all()
    )
    goals = []
    for e in events:
        if e.event_type == "Shot" and e.outcome == "Goal":
            goals.append((e.team_name, e.minute))
        elif e.event_type == "Own Goal For":
            goals.append((e.team_name, e.minute))
    return goals


def build_training_frame(session: Session, minute_cap: int = 90) -> pd.DataFrame:
    rows = []
    matches = session.query(Match).all()

    for match in matches:
        goals = _goal_events_for_match(session, match.id)

        total_home = sum(1 for team, _ in goals if team == match.home_team)
        total_away = sum(1 for team, _ in goals if team == match.away_team)
        if total_home != match.home_score or total_away != match.away_score:
            print(
                f"Warning: goal event count ({total_home}-{total_away}) does not match "
                f"recorded score ({match.home_score}-{match.away_score}) for match {match.id} "
                f"({match.home_team} vs {match.away_team}). Check for extra time or own-goal edge cases."
            )

        if match.home_score > match.away_score:
            home_outcome, away_outcome = 2, 0
        elif match.home_score < match.away_score:
            home_outcome, away_outcome = 0, 2
        else:
            home_outcome, away_outcome = 1, 1

        for minute in range(0, minute_cap + 1):
            home_goals = sum(1 for team, m in goals if team == match.home_team and m <= minute)
            away_goals = sum(1 for team, m in goals if team == match.away_team and m <= minute)
            score_diff = home_goals - away_goals

            rows.append({"match_id": match.id, "minute": minute, "score_diff": score_diff, "outcome": home_outcome})
            rows.append({"match_id": match.id, "minute": minute, "score_diff": -score_diff, "outcome": away_outcome})

    return pd.DataFrame(rows)


def _feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame()
    X["score_diff"] = df["score_diff"]
    X["minutes_remaining"] = 90 - df["minute"]
    X["score_diff_x_time"] = X["score_diff"] * X["minutes_remaining"]
    return X


def train_model(df: pd.DataFrame) -> LogisticRegression:
    X = _feature_frame(df)
    y = df["outcome"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)
    print(f"Holdout accuracy: {accuracy_score(y_test, preds):.3f}")
    print(f"Holdout log loss: {log_loss(y_test, probs, labels=model.classes_):.3f}")

    return model


def save_model(model: LogisticRegression) -> None:
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


def load_model() -> LogisticRegression:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No trained model at {MODEL_PATH}. Run with --train first.")
    return joblib.load(MODEL_PATH)


def predict_win_probability(model: LogisticRegression, score_diff: int, minute: int) -> dict[str, float]:
    row = pd.DataFrame([{"score_diff": score_diff, "minute": minute}])
    X = _feature_frame(row)
    probs = model.predict_proba(X)[0]
    label_map = {0: "loss", 1: "draw", 2: "win"}
    return {label_map[c]: float(p) for c, p in zip(model.classes_, probs)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/query the win-probability model.")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--predict", nargs=2, metavar=("SCORE_DIFF", "MINUTE"), type=int)
    args = parser.parse_args()

    if args.train:
        session = SessionLocal()
        try:
            df = build_training_frame(session)
            n_matches = df["match_id"].nunique()
            print(f"Built training frame: {len(df)} rows from {n_matches} match(es).")
            if n_matches < 10:
                print("Warning: fewer than 10 matches ingested - this model will be crude. Ingest more before trusting it.")
            model = train_model(df)
            save_model(model)
        finally:
            session.close()

    if args.predict:
        score_diff, minute = args.predict
        model = load_model()
        probs = predict_win_probability(model, score_diff, minute)
        print(f"score_diff={score_diff}, minute={minute} -> {probs}")


if __name__ == "__main__":
    main()
