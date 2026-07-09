"""Training statistics. One implementation shared by the stats endpoints and
the dashboard, so the numbers can never drift between views."""
from collections import Counter
from datetime import date, timedelta

from sqlalchemy.orm import Session as DBSession

from app import models


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def session_stats_for_owner(db: DBSession, owner_user_id: str) -> dict:
    """Attendance-based session statistics.

    Only sessions with attended=True count. The streak is the number of
    consecutive calendar weeks (Mon–Sun, current week first) containing at
    least one attended session — no session yet this week means streak 0.
    """
    today = date.today()
    week_start = _week_start(today)
    month_start = today.replace(day=1)

    attended = (
        db.query(models.Session)
        .filter(
            models.Session.owner_user_id == owner_user_id,
            models.Session.attended.is_(True),
        )
        .all()
    )
    attended_dates = [s.date for s in attended]
    total_minutes = sum(s.duration_minutes or 0 for s in attended)

    def count_since(cutoff: date) -> int:
        return sum(1 for d in attended_dates if d >= cutoff)

    streak = 0
    date_set = set(attended_dates)
    check_week = week_start
    while any(check_week <= d <= check_week + timedelta(days=6) for d in date_set):
        streak += 1
        check_week -= timedelta(weeks=1)

    last_30 = count_since(today - timedelta(days=30))
    last_90 = count_since(today - timedelta(days=90))

    return {
        "total_sessions": len(attended),
        "total_minutes": total_minutes,
        "sessions_this_week": count_since(week_start),
        "sessions_this_month": count_since(month_start),
        "current_streak": streak,
        "last_30_day_count": last_30,
        "last_90_day_count": last_90,
        "last_30_day_rate": round(last_30 / 30 * 7, 1),
        "last_90_day_rate": round(last_90 / 90 * 7, 1),
    }


WIN_OUTCOMES = ("submission_win", "points_win")
LOSS_OUTCOMES = ("submission_loss", "points_loss")


def roll_stats_for_owner(db: DBSession, owner_user_id: str) -> dict:
    """Roll outcome statistics.

    Legacy outcomes (win/loss/competitive) are excluded from the top-level
    W/L/draw buckets but fall into the per-partner "draws" bucket — frozen
    v1 math.
    """
    rolls = (
        db.query(models.RollLog)
        .filter(models.RollLog.owner_user_id == owner_user_id)
        .all()
    )
    if not rolls:
        return {"total_rolls": 0}

    total = len(rolls)
    outcomes = Counter(r.outcome for r in rolls)
    wins = sum(outcomes.get(o, 0) for o in WIN_OUTCOMES)
    losses = sum(outcomes.get(o, 0) for o in LOSS_OUTCOMES)

    subs_scored = Counter(r.submission_scored for r in rolls if r.submission_scored)
    subs_received = Counter(r.submission_received for r in rolls if r.submission_received)
    positions_held = Counter(
        position for r in rolls for position in (r.dominant_positions_held or [])
    )
    positions_given = Counter(
        position for r in rolls for position in (r.dominant_positions_given or [])
    )

    partner_stats: dict[str, dict[str, int]] = {}
    for roll in rolls:
        bucket = partner_stats.setdefault(
            roll.partner, {"wins": 0, "losses": 0, "draws": 0, "total": 0}
        )
        bucket["total"] += 1
        if roll.outcome in WIN_OUTCOMES:
            bucket["wins"] += 1
        elif roll.outcome in LOSS_OUTCOMES:
            bucket["losses"] += 1
        else:
            bucket["draws"] += 1

    return {
        "total_rolls": total,
        "wins": wins,
        "losses": losses,
        "draws": outcomes.get("draw", 0),
        "win_rate": round(wins / total * 100, 1) if total else 0,
        "top_submissions_scored": subs_scored.most_common(5),
        "top_submissions_received": subs_received.most_common(5),
        "top_positions_held": positions_held.most_common(5),
        "top_positions_given": positions_given.most_common(5),
        "partner_breakdown": partner_stats,
    }
