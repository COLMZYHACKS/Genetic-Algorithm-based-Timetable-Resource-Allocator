"""
Refactored fitness function.

This module provides:
- `fitness(individual)` -> numeric penalty (lower is better) used by the GA (backwards-compatible).
- `get_fitness_breakdown(individual)` -> structured breakdown with hard/soft counts, penalties and a normalized quality score (0-100).

Design goals:
- Keep GA behavior: fitness() returns a numeric value where lower==better.
- Use dynamic scaling so a single hard violation always dominates soft improvements.
- Preserve raw counts for reporting.
"""

from typing import Any, Dict, List, Tuple
from services.time_utils import parse_time_value


# Configuration - relative weights (kept modest and documented)
HARD_WEIGHTS = {
    "lecturer_conflict": 5.0,  # two classes for same lecturer at same slot
    "room_conflict": 5.0,      # two classes assigned to same room at same slot
    "group_conflict": 5.0,     # two classes for same student group at same slot
    "capacity_violation": 3.0, # students > room capacity
    "missing_assignment": 2.0, # missing room/day/period
    "invalid_time": 2.0
}

SOFT_WEIGHTS = {
    "late_class": 0.5,         # class starts after preferred time (e.g., after 17:00)
    "room_preference": 0.25,   # small preference metrics (placeholder)
    "unused_room": 0.1
}


def _read_gene(g: Any) -> Dict[str, Any]:
    """Support both dict-based and tuple/list-based gene encodings.

    Expected dict keys: course, lecturer, room, day, period, group, capacity, students
    Expected tuple order (legacy): (course, lecturer, room, period, ..., group, capacity, students)
    """
    if isinstance(g, dict):
        return {
            "course": g.get("course"),
            "lecturer": g.get("lecturer"),
            "room": g.get("room"),
            "day": g.get("day"),
            "period": g.get("period"),
            "group": g.get("group"),
            "capacity": g.get("capacity") or 0,
            "students": g.get("students") or 0,
        }
    try:
        # tolerant unpacking for tuple-like legacy genes
        course = g[0]
        lecturer = g[1]
        room = g[2]
        period = g[3]
        # some legacy formats include duration etc; group often later
        group = g[5] if len(g) > 5 else None
        capacity = g[6] if len(g) > 6 else 0
        students = g[7] if len(g) > 7 else 0
        # try to extract day from period when possible (e.g. "Monday 07:00-09:00")
        day = None
        if isinstance(period, str) and " " in period:
            parts = period.split(" ", 1)
            day = parts[0]
        return {
            "course": course,
            "lecturer": lecturer,
            "room": room,
            "day": day,
            "period": period,
            "group": group,
            "capacity": capacity or 0,
            "students": students or 0,
        }
    except Exception:
        # Malformed gene
        return {
            "course": None,
            "lecturer": None,
            "room": None,
            "day": None,
            "period": None,
            "group": None,
            "capacity": 0,
            "students": 0,
        }


def _is_late_period(period: Any) -> bool:
    # period may be like "07:00-09:00" or "Monday 07:00-09:00"
    try:
        if isinstance(period, str):
            if " " in period:
                _, time_part = period.split(" ", 1)
            else:
                time_part = period
            start_str = time_part.split("-", 1)[0]
            start_min = parse_time_value(start_str)
            return start_min is not None and start_min > 17 * 60
    except Exception:
        return False
    return False


def evaluate(individual: List[Any]) -> Dict[str, Any]:
    """Return a detailed breakdown (counts, penalties) but do NOT change GA behavior.

    The GA will call `fitness()` which returns a numeric value derived from this breakdown.
    """
    counts = {
        "lecturer_conflicts": 0,
        "room_conflicts": 0,
        "group_conflicts": 0,
        "capacity_violations": 0,
        "missing_assignments": 0,
        "invalid_time": 0,
        "late_classes": 0,
    }

    seen_lecturer = set()
    seen_room = set()
    seen_group = set()

    # Safe-guard empty timetable: treat as an invalid schedule with a missing assignment
    if not individual:
        counts["missing_assignments"] = 1
        breakdown = {
            "counts": counts,
            "hard_penalty": (
                counts["missing_assignments"] * HARD_WEIGHTS["missing_assignment"]
            ),
            "soft_penalty": 0.0,
        }
        return breakdown

    for gene in individual:
        g = _read_gene(gene)
        lecturer = g.get("lecturer")
        room = g.get("room")
        day = g.get("day")
        period = g.get("period")
        group = g.get("group")
        capacity = g.get("capacity") or 0
        students = g.get("students") or 0

        # Missing/invalid assignments
        if not day or not period:
            counts["missing_assignments"] += 1

        # Capacity violations
        if room is not None and students > capacity:
            counts["capacity_violations"] += 1

        # Key for conflicts - use exact slot matching (string equality)
        key_lect = (lecturer, day, period)
        if lecturer and key_lect in seen_lecturer:
            counts["lecturer_conflicts"] += 1
        seen_lecturer.add(key_lect)

        key_room = (room, day, period)
        if room is not None and key_room in seen_room:
            counts["room_conflicts"] += 1
        seen_room.add(key_room)

        key_group = (group, day, period)
        if group and key_group in seen_group:
            counts["group_conflicts"] += 1
        seen_group.add(key_group)

        # Soft: late classes
        if _is_late_period(period):
            counts["late_classes"] += 1

    # Compute penalty sums (weighted)
    hard_penalty = (
        counts["lecturer_conflicts"] * HARD_WEIGHTS["lecturer_conflict"]
        + counts["room_conflicts"] * HARD_WEIGHTS["room_conflict"]
        + counts["group_conflicts"] * HARD_WEIGHTS["group_conflict"]
        + counts["capacity_violations"] * HARD_WEIGHTS["capacity_violation"]
        + counts["missing_assignments"] * HARD_WEIGHTS["missing_assignment"]
        + counts["invalid_time"] * HARD_WEIGHTS["invalid_time"]
    )

    soft_penalty = (
        counts["late_classes"] * SOFT_WEIGHTS["late_class"]
    )

    breakdown = {
        "counts": counts,
        "hard_penalty": float(hard_penalty),
        "soft_penalty": float(soft_penalty),
    }
    return breakdown


def get_fitness_breakdown(individual: List[Any]) -> Dict[str, Any]:
    """Return a user-friendly breakdown including a normalized quality score (0-100).

    This function is safe to call from API endpoints for human reporting.
    """
    breakdown = evaluate(individual)
    counts = breakdown["counts"]
    hard_penalty = breakdown["hard_penalty"]
    soft_penalty = breakdown["soft_penalty"]

    n = max(1, len(individual))
    # Estimate maximum plausible soft penalty for normalization
    max_soft_possible = n * max(SOFT_WEIGHTS.values())

    # Hierarchical scoring: zero hard violations always preferred.
    if hard_penalty == 0:
        # Soft quality in [0,1]
        soft_quality = 1.0 - (soft_penalty / (max_soft_possible + 1e-6))
        soft_quality = max(0.0, min(1.0, soft_quality))
        # Map to (0.5, 1.0] so zero-hard solutions occupy top half of the scale
        quality = 0.5 + 0.5 * soft_quality
    else:
        # Penalize by hard_penalty. Map to [0,0.5)
        hard_quality = 1.0 / (1.0 + hard_penalty)
        quality = 0.5 * max(0.0, min(1.0, hard_quality))

    fitness_percent = round(quality * 100.0, 2)

    # For GA numeric fitness (lower is better), compute total_penalty such that
    # any hard penalty dominates soft penalties. We create a dynamic scale so we
    # don't rely on arbitrary large constants.
    soft_upper = max(1.0, max_soft_possible)
    hard_scale = (soft_upper * 1.0) + 1.0
    total_penalty = hard_penalty * hard_scale + soft_penalty

    return {
        "fitness": fitness_percent,
        "total_penalty": float(total_penalty),
        "hard_penalty": float(hard_penalty),
        "soft_penalty": float(soft_penalty),
        "violations": counts,
    }


def fitness(individual: List[Any]) -> float:
    """Return numeric penalty used by the GA (lower is better).

    This preserves backwards-compatibility: algorithms that minimize fitness
    continue to work. Use `get_fitness_breakdown()` to obtain the human-friendly
    0-100 score and detailed counts.
    """
    bd = get_fitness_breakdown(individual)
    return float(bd["total_penalty"])