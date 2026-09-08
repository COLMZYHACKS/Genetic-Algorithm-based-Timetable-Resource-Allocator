from models import Lecturer, Room, Timeslot, Course, ExamPeriod, Exam
import pandas as pd
import json
import re

DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


def sort_day_labels(days):
    seen = []
    for day in days:
        value = str(day).strip()
        if value not in seen:
            seen.append(value)

    def key_fn(value):
        date_match = re.match(r"^(\d{2})-(\d{2})$", value)
        if date_match:
            return (1, int(date_match.group(1)), int(date_match.group(2)))
        if value in DAY_ORDER:
            return (0, DAY_ORDER.index(value), 0)
        return (2, value, 0)

    return sorted(seen, key=key_fn)


def get_lecturers_data():
    lecturers = Lecturer.query.all()
    return [{"id": l.id, "name": l.name, "unavailable_slots": json.loads(l.unavailable_slots) if l.unavailable_slots else []} for l in lecturers]

def get_rooms_data():
    rooms = Room.query.all()
    return [{"id": r.id, "capacity": r.capacity} for r in rooms]

def get_timeslots_data():
    timeslots = Timeslot.query.all()
    return [{"id": t.id, "day": t.day, "time": t.time} for t in timeslots]

def get_exam_periods_data():
    exam_periods = ExamPeriod.query.all()
    return [{"id": ep.id, "day": ep.day, "time": ep.time, "duration": ep.duration} for ep in exam_periods]

def get_courses_dataframe():
    courses = Course.query.all()
    data = []
    for c in courses:
        data.append({
            "course": c.name,
            "lecturer": c.lecturer.name,
            "group": c.group,
            "students": c.students,
            "capacity": c.capacity,
            "room": c.room.id if c.room else None
        })
    return pd.DataFrame(data)

def get_exams_dataframe():
    exams = Exam.query.all()
    data = []
    exam_periods = get_exam_periods_data()
    available_dates = [ep["day"] for ep in exam_periods] if exam_periods else []
    unique_dates = sort_day_labels(available_dates) if available_dates else ["01-06", "01-07", "01-08", "01-09", "01-10"]
    for index, e in enumerate(exams):
        data.append({
            "course": e.course.name,
            "lecturer": e.course.lecturer.name,
            "group": e.course.group,
            "students": e.course.students,
            "duration": e.duration,
            "required_room_type": e.required_room_type,
            "day": unique_dates[index % len(unique_dates)]
        })
    return pd.DataFrame(data)