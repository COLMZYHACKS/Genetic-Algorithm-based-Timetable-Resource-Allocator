from flask import Blueprint, request, jsonify
from services.parser import parse_file, parse_exam_file
from services.ga import run_ga
from services.ga_engine import run_exam_ga
from services.database_service import get_courses_dataframe, get_exams_dataframe
from services.fitness import get_fitness_breakdown
import os

generate_bp = Blueprint("generate", __name__)

@generate_bp.route("/generate", methods=["OPTIONS"])
def options_generate():
    return '', 200

@generate_bp.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json or {}
        print("REQUEST DATA:", data)

        timetable_type = data.get("type", "course")
        if timetable_type == "exam":
            return generate_exam_timetable(data)
        return generate_teaching_timetable(data)

    except Exception as e:
        print("ERROR IN GENERATE:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def parse_boolean(value):
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return bool(value)


def get_column_map(data):
    return data.get("columns") or data.get("columnMap") or {}


def generate_teaching_timetable(data):
    use_database = parse_boolean(data.get("use_database") or data.get("useDatabase", False))
    path = data.get("path")
    column_map = get_column_map(data)

    if use_database:
        df = get_courses_dataframe()
        print("USING DATABASE COURSE DATA")
    else:
        if not path or (isinstance(path, str) and path.strip() == ""):
            return jsonify({"error": "Invalid file path"}), 400

        path = os.path.abspath(path)
        print("ABSOLUTE PATH:", path)

        try:
            df = parse_file(path, column_map)
        except Exception as parse_exc:
            print("FILE PARSE ERROR:", str(parse_exc))
            return jsonify({"error": f"Failed to parse uploaded file: {parse_exc}"}), 400

    if df is None or getattr(df, "empty", False):
        return jsonify({"error": "No course data was found. Please upload a file or populate the database."}), 400

    print("DATAFRAME HEAD:\n", df.head())
    print("COLUMNS:", df.columns)
    print("CSV SCHEDULE DETECTED:", df.attrs.get("csv_has_timeslot_data", False))

    result = run_ga(df)
    fitness_breakdown = get_fitness_breakdown(result)

    formatted = [
        {
            "course": g["course"],
            "lecturer": g["lecturer"],
            "room": g["room"],
            "day": g["day"],
            "period": g["period"],
            "group": g["group"],
            "capacity": g["capacity"],
            "students": g["students"]
        }
        for g in result
    ]

    return jsonify({
        "timetable": formatted,
        "fitness": round(fitness_breakdown["fitness"], 2),
        "fitness_breakdown": fitness_breakdown,
        "score": round(fitness_breakdown["fitness"], 2)
    })


def generate_exam_timetable(data):
    use_database = parse_boolean(data.get("use_database") or data.get("useDatabase", False))
    path = data.get("path")
    column_map = get_column_map(data)

    if use_database:
        df = get_exams_dataframe()
        print("USING DATABASE EXAM DATA")
    else:
        if not path or (isinstance(path, str) and path.strip() == ""):
            return jsonify({"error": "Invalid file path"}), 400

        path = os.path.abspath(path)
        print("ABSOLUTE PATH:", path)

        try:
            df = parse_exam_file(path, column_map)
        except Exception as parse_exc:
            print("FILE PARSE ERROR:", str(parse_exc))
            return jsonify({"error": f"Failed to parse uploaded file: {parse_exc}"}), 400

    if df is None or getattr(df, "empty", False):
        return jsonify({"error": "No exam data was found. Please upload a file or populate the database."}), 400

    if "day" not in df.columns:
        df["day"] = "Day1"

    print("EXAM DATAFRAME HEAD:\n", df.head())
    print("EXAM COLUMNS:", df.columns)
    print("EXAM COURSE COUNT:", len(df))
    print("EXAM UNIQUE DAYS:", sorted(df["day"].dropna().astype(str).str.strip().replace("", "Day1").unique()))

    result, exam_periods = run_exam_ga(df)
    fitness_breakdown = get_fitness_breakdown(result)

    formatted = []
    for g in result:
        period_info = exam_periods[g[3]] if 0 <= g[3] < len(exam_periods) else None
        time_value = period_info["time"] if period_info else "Unknown"
        formatted.append({
            "course": g[0],
            "lecturer": g[1],
            "room": g[2],
            "day": period_info["day"] if period_info else "Unknown",
            "period": time_value,
            "time": time_value,
            "duration": period_info["duration"] if period_info else 0,
            "group": g[4],
            "students": g[5]
        })

    return jsonify({
        "timetable": formatted,
        "fitness": round(fitness_breakdown["fitness"], 2),
        "fitness_breakdown": fitness_breakdown,
        "score": round(fitness_breakdown["fitness"], 2)
    })
