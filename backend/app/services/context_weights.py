"""Hand-set weights for aggregating ratings across matches of different
importance. Deliberately NOT applied to the raw per-match PlayerMatchRating
value - that number stays a self-contained account of one match. These
weights only apply when combining multiple matches into a summary (season
average, etc.)."""

STAGE_WEIGHTS: dict[str | None, float] = {
    "Final": 1.5,
    "3rd Place Final": 1.2,
    "Semi-finals": 1.3,
    "Quarter-finals": 1.15,
    "Round of 16": 1.1,
    "1st Round": 1.0,
    "1st Group Stage": 1.0,
    "Group Stage": 1.0,
    "Regular Season": 1.0,
}
DEFAULT_STAGE_WEIGHT = 1.0

# Tournament tier, not popularity or revenue. Top-flight domestic leagues
# (men's or women's) sit at the same baseline weight - a top-level league
# match is a top-level league match regardless of which league's media
# profile is larger. International tournaments are weighted above domestic
# league play since they concentrate a nation's best players against other
# nations' best, typically with higher stakes per match played.
COMPETITION_WEIGHTS: dict[str, float] = {
    "International - FIFA World Cup": 1.5,
    "Europe - Champions League": 1.4,
    "Europe - UEFA Euro": 1.35,
    "South America - Copa America": 1.3,
    "Africa - African Cup of Nations": 1.3,
    "International - FIFA U20 World Cup": 0.9,
    "Germany - 1. Bundesliga": 1.0,
    "Spain - La Liga": 1.0,
    "England - FA Women's Super League": 1.0,
    "Germany - Frauen Bundesliga": 1.0,
    "Spain - Copa del Rey": 0.9,
}
DEFAULT_COMPETITION_WEIGHT = 1.0


def stage_weight(stage: str | None) -> float:
    return STAGE_WEIGHTS.get(stage, DEFAULT_STAGE_WEIGHT)


def competition_weight(competition: str | None) -> float:
    return COMPETITION_WEIGHTS.get(competition, DEFAULT_COMPETITION_WEIGHT)


def context_weight(competition: str | None, stage: str | None) -> float:
    return competition_weight(competition) * stage_weight(stage)
