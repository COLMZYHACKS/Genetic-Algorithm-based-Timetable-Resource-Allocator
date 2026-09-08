from flask import Blueprint, request, jsonify
from services.parser import parse_file, parse_exam_file
from services.ga_engine import run_ga, run_exam_ga, TIMESLOTS
from services.database_service import get_exam_periods_data, get_courses_dataframe, get_exams_dataframe
from services.time_utils import format_minutes, parse_time_range

timetable_bp = Blueprint("timetable", __name__)

@timetable_bp.route("/generate", methods=["OPTIONS"])
def options_generate():
    return '', 200

@timetable_bp.route("/generate", methods=["POST"])
def generate():
    data = request.json
    timetable_type = data.get("type", "course")  # Default to course timetable

    if timetable_type == "exam":
        return generate_exam_timetable(data)
    else:
        return generate_course_timetable(data)

def generate_course_timetable(data):
    use_database = bool(data.get("use_database", False))
    filepath = data.get("path")
    column_map = data.get("columns", {})

    if use_database:
        df = get_courses_dataframe()
    else:
        if not filepath:
            return jsonify({"error": "path is required when not using database data"}), 400

        try:
            df = parse_file(filepath, column_map)
        except (KeyError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"unexpected error: {exc}"}), 500

    result = run_ga(df)

    formatted = []

    for g in result:
        timeslot_idx = g[3]
        duration = g[4]
        if 0 <= timeslot_idx < len(TIMESLOTS):
            timeslot = TIMESLOTS[timeslot_idx]
            day = timeslot['day']
            start, _ = parse_time_range(timeslot['time'])
            if start is not None:
                period = f"{format_minutes(start)}-{format_minutes(start + duration)}"
            else:
                period = timeslot['time']
        else:
            day = "Unknown"
            period = "Unknown"

        formatted.append({
            "course": g[0],
            "lecturer": g[1],
            "room": g[2],
            "day": day,
            "period": period,
            "group": g[5],
            "capacity": g[6],
            "students": g[7]
        })

    return jsonify({"timetable": formatted})

def generate_exam_timetable(data):
    use_database = bool(data.get("use_database", False))
    filepath = data.get("path")
    column_map = data.get("columns", {})

    if use_database:
        df = get_exams_dataframe()
    else:
        if not filepath:
            return jsonify({"error": "path is required when not using database data"}), 400

        try:
            df = parse_exam_file(filepath, column_map)
        except (KeyError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"unexpected error: {exc}"}), 500

    result, exam_periods = run_exam_ga(df)
    formatted = []

    for g in result:
        exam_period_idx = g[3]
        period_info = exam_periods[exam_period_idx] if 0 <= exam_period_idx < len(exam_periods) else None
        day = period_info['day'] if period_info else "Unknown"
        time = period_info['time'] if period_info else "Unknown"
        duration = period_info['duration'] if period_info else 0

        formatted.append({
            "course": g[0],
            "lecturer": g[1],
            "room": g[2],
            "day": day,
            "period": time,
            "time": time,
            "duration": duration,
            "group": g[4],
            "students": g[5]
        })

    return jsonify({"timetable": formatted})