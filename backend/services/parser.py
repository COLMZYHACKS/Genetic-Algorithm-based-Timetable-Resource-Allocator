import pandas as pd
import re

DAY_NAMES = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]

COLUMN_SYNONYMS = {
    "course": ["course", "course_full", "course_code", "subject", "module", "class", "title"],
    "lecturer": ["lecturer", "teacher", "instructor", "professor", "staff"],
    "room": ["room", "hall", "venue", "location", "classroom", "lecture hall", "auditorium"],
    "capacity": ["capacity", "room_capacity", "room_size", "size", "seats", "max_students"],
    "students": ["students", "class_size", "studentcount", "student_count", "enrollment", "count", "number", "enrolled"],
    "group": ["group", "batch", "section", "class_group", "cohort", "studentgroup", "student_group"],
    "day": ["day", "weekday", "date"],
    "period": ["period", "timeslot", "time_slot", "session", "slot", "time"],
    "start_time": ["start_time", "start time", "start", "begin", "from"],
    "end_time": ["end_time", "end time", "end", "finish", "to"],
    "slot": ["slot", "slot_index", "slot_number", "slot_id"]
}

DEFAULT_PERIODS = [
    "08:00-10:00",
    "10:00-12:00",
    "13:00-15:00",
    "15:00-17:00"
]


def normalize_column_name(name):
    return re.sub(r"[\s\-]+", "_", str(name).strip().lower())


def detect_column(columns, keywords):
    normalized_keywords = [normalize_column_name(k) for k in keywords]
    for col in columns:
        normalized = normalize_column_name(col)
        if normalized in normalized_keywords:
            return col
    for col in columns:
        normalized = normalize_column_name(col)
        if any(keyword in normalized for keyword in normalized_keywords):
            return col
    return None


def normalize_period_string(period_value):
    if period_value is None:
        return None

    text = str(period_value).strip()
    # Preserve day prefix if provided in timeslot strings like "Monday_08:00-10:00"
    if "_" in text:
        day_part, rest = text.split("_", 1)
        if normalize_column_name(day_part) in DAY_NAMES:
            rest = rest.strip()
            normalized_rest = normalize_period_string(rest)
            return f"{day_part.title()}_{normalized_rest}" if normalized_rest else text

    parts = [p.strip() for p in text.split("-")]
    if len(parts) != 2:
        return text

    def parse_time(comp):
        comp = comp.replace(" ", "").replace(":00", "")
        if comp == "":
            return None
        time_parts = comp.split(":")
        try:
            if len(time_parts) == 1:
                hour = int(time_parts[0])
                minute = 0
            else:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
        except ValueError:
            return None
        return hour * 60 + minute

    start = parse_time(parts[0])
    end = parse_time(parts[1])
    if start is None or end is None:
        return text

    return f"{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}"


def split_day_from_period(period_value):
    if period_value is None:
        return None, None

    text = str(period_value).strip()
    if not text:
        return None, None

    if "_" in text:
        day_part, rest = text.split("_", 1)
        if normalize_column_name(day_part) in DAY_NAMES:
            return day_part.title(), rest.strip()

    parts = text.split(" ", 1)
    if len(parts) == 2 and normalize_column_name(parts[0]) in DAY_NAMES:
        return parts[0].title(), parts[1].strip()

    return None, text


def normalize_exam_day(day):
    if day is None:
        return "Day1"
    text = str(day).strip()
    if text == "":
        return "Day1"

    normalized = text.lower().replace('.', '').replace(',', '').strip()
    day_names = {
        "monday": "Monday",
        "mon": "Monday",
        "tuesday": "Tuesday",
        "tue": "Tuesday",
        "tues": "Tuesday",
        "wednesday": "Wednesday",
        "wed": "Wednesday",
        "thursday": "Thursday",
        "thu": "Thursday",
        "thurs": "Thursday",
        "friday": "Friday",
        "fri": "Friday",
        "saturday": "Saturday",
        "sat": "Saturday",
        "sunday": "Sunday",
        "sun": "Sunday"
    }
    if normalized in day_names:
        return day_names[normalized]

    # Support numeric day labels like Day 1 or 1
    if normalized.isdigit():
        return f"Day{int(normalized)}"

    day_match = re.match(r"^day[\s_-]*(\d+)$", normalized)
    if day_match:
        return f"Day{int(day_match.group(1))}"

    # Support month/day or month-day dates without year
    date_match = re.match(r"^(\d{1,2})[/-](\d{1,2})$", normalized)
    if date_match:
        month = int(date_match.group(1))
        day = int(date_match.group(2))
        return f"{month:02d}-{day:02d}"

    for key, value in day_names.items():
        if normalized.startswith(key):
            return value

    return text.title()


def parse_exam_file(path, column_map=None):
    # Normalize exam upload columns for different input formats.
    # Exam generation only uses course, lecturer, room, students, group, and day.
    if path.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    df.columns = df.columns.str.strip()
    original_columns = list(df.columns)

    rename_map = {}
    for logical_name in ["course", "lecturer", "room", "students", "group", "day", "capacity"]:
        explicit_column = None
        if isinstance(column_map, dict) and logical_name in column_map and column_map[logical_name]:
            explicit_column = column_map[logical_name]
            if explicit_column not in df.columns:
                raise KeyError(f"Mapped column '{explicit_column}' for '{logical_name}' not found in file")
            rename_map[explicit_column] = logical_name
            continue

        detected = detect_column(df.columns, COLUMN_SYNONYMS.get(logical_name, []))
        if detected:
            rename_map[detected] = logical_name

    df = df.rename(columns=rename_map)

    if "day" not in df.columns:
        df["day"] = "Day1"
    else:
        df["day"] = df["day"].apply(lambda v: normalize_exam_day(v) if pd.notna(v) else "Day1")
        if df["day"].isna().all() or (df["day"].astype(str).str.strip() == "").all():
            df["day"] = "Day1"

    # Ignore all CSV time-related columns because exam timetable uses fixed institutional times.
    for ignored in ["period", "timeslot", "time", "start_time", "end_time", "slot"]:
        if ignored in df.columns:
            df = df.drop(columns=[ignored])

    print("EXAM ORIGINAL COLUMNS:", original_columns)
    print("EXAM NORMALIZED COLUMNS:", list(df.columns))

    return df


def parse_file(path, column_map=None):
    # Detect and normalize CSV columns for uploads.
    # Course and exam schedules use fixed institutional timeslots, so any CSV
    # time-related columns are ignored after parsing.
    if path.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    df.columns = df.columns.str.strip()
    original_columns = list(df.columns)

    rename_map = {}
    for logical_name, keywords in COLUMN_SYNONYMS.items():
        explicit_column = None
        if isinstance(column_map, dict) and logical_name in column_map and column_map[logical_name]:
            explicit_column = column_map[logical_name]
            if explicit_column not in df.columns:
                raise KeyError(f"Mapped column '{explicit_column}' for '{logical_name}' not found in file")
            rename_map[explicit_column] = logical_name
            continue

        detected = detect_column(df.columns, keywords)
        if detected:
            rename_map[detected] = logical_name

    df = df.rename(columns=rename_map)

    # If a timeslot column exists as a slot index, prefer actual start/end time values when available.
    if "period" not in df.columns and "slot" in df.columns:
        if "start_time" in df.columns and "end_time" in df.columns:
            def build_period_from_times(row):
                start = str(row["start_time"]).strip()
                end = str(row["end_time"]).strip()
                if start and end:
                    if "day" in df.columns and pd.notna(row.get("day")) and str(row["day"]).strip() != "":
                        return f"{str(row['day']).strip()}_{start}-{end}"
                    return f"{start}-{end}"
                return None
            df["period"] = df.apply(build_period_from_times, axis=1)
        else:
            if "day" in df.columns:
                df["period"] = df.apply(
                    lambda row: f"{str(row['day'])}_{str(row['slot'])}" if pd.notna(row['slot']) and str(row['slot']).strip() != "" else None,
                    axis=1
                )
            else:
                df["period"] = df["slot"].astype(str).replace("nan", "")

    # If the CSV has day, start_time and end_time columns, construct a self-contained period.
    if "period" not in df.columns and "start_time" in df.columns and "end_time" in df.columns:
        def build_period(row):
            start = str(row["start_time"]).strip()
            end = str(row["end_time"]).strip()
            if start and end:
                if "day" in df.columns and pd.notna(row.get("day")) and str(row["day"]).strip() != "":
                    return f"{str(row['day']).strip()}_{start}-{end}"
                return f"{start}-{end}"
            return None
        df["period"] = df.apply(build_period, axis=1)

    # If the file contains an explicit timeslot-like column, prefer that value.
    if "period" in df.columns:
        df["period"] = df["period"].apply(lambda v: v if pd.notna(v) else None)

    # Normalize day and period when the timeslot string embeds the day.
    if "period" in df.columns:
        if "day" not in df.columns:
            df["day"] = df["period"].apply(lambda v: split_day_from_period(v)[0] if pd.notna(v) else None)
        df["period"] = df.apply(
            lambda row: split_day_from_period(row["period"])[1] if pd.notna(row["period"]) else row["period"],
            axis=1
        )

    # If no day column but a slot exists, keep slot as a period indicator.
    if "day" not in df.columns and "slot" in df.columns and "period" not in df.columns:
        df["period"] = df["slot"].astype(str)

    # Ignore only raw time fields after building the normalized period column.
    for ignored in ["time", "start_time", "end_time", "slot"]:
        if ignored in df.columns:
            df = df.drop(columns=[ignored])

    print("ORIGINAL COLUMNS:", original_columns)
    print("NORMALIZED COLUMNS:", list(df.columns))

    return df