import json
import os
from services.time_utils import parse_time_range, times_overlap

# Load reference data for constraints
data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
with open(os.path.join(data_dir, 'lecturers.json'), 'r') as f:
    LECTURERS = json.load(f)
with open(os.path.join(data_dir, 'timeslots.json'), 'r') as f:
    TIMESLOTS = json.load(f)

# For exams, we'll need exam periods data
exam_periods_path = os.path.join(data_dir, 'exam_periods.json')
if os.path.exists(exam_periods_path):
    with open(exam_periods_path, 'r') as f:
        EXAM_PERIODS = json.load(f)
else:
    EXAM_PERIODS = []


def check_hard_constraints(individual):
    penalty = 0

    lecturer_time = {}
    room_time = {}
    group_time = {}

    # Create lecturer availability map
    lecturer_availability = {}
    for lect in LECTURERS:
        lecturer_availability[lect['name']] = set(lect.get('unavailable_slots', []))

    for gene in individual:
        course, lecturer, room, period, duration, group, room_capacity, students = gene

        # Parse period: assume format "Day HH:MM-HH:MM"
        try:
            day_part, time_part = period.split(' ', 1)
            start_str, end_str = time_part.split('-')
            start = parse_time_range(f"{start_str}-{end_str}")[0]
            end = start + duration
            day = day_part
        except:
            penalty += 100
            continue

        # Lecturer unavailable - for now, skip if no timeslot_id
        # if lecturer in lecturer_availability and timeslot_id in lecturer_availability[lecturer]:
        #     penalty += 100

        # Lecturer clash
        existing_lecturer_times = lecturer_time.setdefault((lecturer, day), [])
        for existing_start, existing_end in existing_lecturer_times:
            if times_overlap(start, end, existing_start, existing_end):
                penalty += 1000
                break

        # Room clash (only if room is assigned)
        if room is not None:
            existing_room_times = room_time.setdefault((room, day), [])
            for existing_start, existing_end in existing_room_times:
                if times_overlap(start, end, existing_start, existing_end):
                    penalty += 1000
                    break

        # Student clash
        existing_group_times = group_time.setdefault((group, day), [])
        for existing_start, existing_end in existing_group_times:
            if times_overlap(start, end, existing_start, existing_end):
                penalty += 1000
                break

        # Capacity violation (only if room is assigned)
        if room is not None and students > room_capacity:
            penalty += 200

        # Penalty for unassigned room
        if room is None:
            penalty += 100

        lecturer_time[(lecturer, day)].append((start, end))
        if room is not None:
            room_time[(room, day)].append((start, end))
        group_time[(group, day)].append((start, end))

    return penalty

def check_exam_hard_constraints(individual):
    penalty = 0

    lecturer_time = {}
    room_time = {}
    student_time = {}  # Track student schedules across exams

    # Create lecturer availability map
    lecturer_availability = {}
    for lect in LECTURERS:
        lecturer_availability[lect['name']] = set(lect.get('unavailable_slots', []))

    for gene in individual:
        course, lecturer, room, exam_period, group, students = gene

        exam_period_data = EXAM_PERIODS[exam_period] if 0 <= exam_period < len(EXAM_PERIODS) else None
        exam_period_id = exam_period_data['id'] if exam_period_data else None
        start, end = parse_time_range(exam_period_data['time']) if exam_period_data else (None, None)
        duration = exam_period_data['duration'] if exam_period_data and exam_period_data.get('duration') else None
        if start is not None and duration:
            end = start + duration
        day = exam_period_data['day'] if exam_period_data else None

        if start is None or end is None or day is None:
            penalty += 100
            continue

        # Lecturer unavailable (assuming exam periods map to timeslot IDs)
        if lecturer in lecturer_availability and exam_period_id in lecturer_availability[lecturer]:
            penalty += 100

        # Lecturer clash
        existing_lecturer_times = lecturer_time.setdefault((lecturer, day), [])
        for existing_start, existing_end in existing_lecturer_times:
            if times_overlap(start, end, existing_start, existing_end):
                penalty += 1000
                break

        # Room clash (only if room is assigned)
        if room is not None:
            existing_room_times = room_time.setdefault((room, day), [])
            for existing_start, existing_end in existing_room_times:
                if times_overlap(start, end, existing_start, existing_end):
                    penalty += 1000
                    break

        # Student clash - check if any student group has overlapping exams
        if (group, day) in student_time:
            for existing_start, existing_end in student_time[(group, day)]:
                if times_overlap(start, end, existing_start, existing_end):
                    penalty += 1000
                    break

        # Capacity violation (only if room is assigned)
        if room is not None and students > 50:  # Assume exam room capacity
            penalty += 200

        # Penalty for unassigned room
        if room is None:
            penalty += 100

        lecturer_time[(lecturer, day)].append((start, end))
        if room is not None:
            room_time[(room, day)].append((start, end))
        student_time.setdefault((group, day), []).append((start, end))

    return penalty