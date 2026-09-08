import random
import json
import os
import re
from functools import lru_cache
from services.fitness_service import fitness, exam_fitness
from services.database_service import get_rooms_data, get_exam_periods_data
from services.parser import normalize_exam_day
from services.time_utils import parse_time_range, get_random_class_duration

POP_SIZE = 100
GENERATIONS = 500
MUTATION_RATE = 0.12

@lru_cache(maxsize=None)
def load_rooms():
    return get_rooms_data()

DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]


def sort_exam_days(days):
    seen = []
    for day in days:
        normalized = normalize_exam_day(day)
        if normalized not in seen:
            seen.append(normalized)

    def parse_date_key(value):
        match = re.match(r"^(\d{2})-(\d{2})$", value)
        if match:
            return (1, int(match.group(1)), int(match.group(2)))
        if value in DAY_ORDER:
            return (0, DAY_ORDER.index(value), 0)
        return (2, value, 0)

    ordered = sorted(seen, key=parse_date_key)
    return ordered


def get_exam_timeslots(days):
    # Fixed exam periods are generated for each detected day.
    # CSV time values are ignored; only day labels are kept.
    exam_template = [
        {"suffix": "07:00-10:00", "duration": 180},
        {"suffix": "11:00-14:00", "duration": 180},
        {"suffix": "15:00-18:00", "duration": 180}
    ]
    periods = []
    for day in days:
        normalized_day = normalize_exam_day(day)
        for slot in exam_template:
            periods.append({
                "day": normalized_day,
                "time": slot["suffix"],
                "duration": slot["duration"]
            })
    return periods

def has_value(value):
    if value is None:
        return False
    text = str(value).strip().lower()
    return text not in ("", "nan", "none")

def get_available_rooms(students, rooms):
    return [room for room in rooms if room['capacity'] >= students]

def create_individual(df, rooms, periods):
    individual = []
    for _, row in df.iterrows():
        explicit_room = row.get("room")
        if has_value(explicit_room):
            room = str(explicit_room)
            room_capacity = row.get("capacity", 0) or 0
        else:
            available_rooms = get_available_rooms(row.get("students", 0), rooms)
            if available_rooms:
                room_entry = random.choice(available_rooms)
                room = room_entry['id']
                room_capacity = room_entry['capacity']
            else:
                room = None
                room_capacity = 0

        period = row.get("period") or row.get("time")
        if period:
            duration = get_random_class_duration(None)
            period = str(period)
        else:
            period = random.choice(periods)
            start, _ = parse_time_range(period)
            duration = get_random_class_duration(start)

        gene = {
            "course": row.get("course"),
            "lecturer": row.get("lecturer"),
            "room": room,
            "day": row.get("day") or "",
            "period": period,
            "group": row.get("group", "default"),
            "capacity": row.get("capacity", 100),
            "students": row.get("students", 0),
            "duration": duration
        }
        individual.append(gene)
    return individual

def create_population(df, rooms, periods):
    return [create_individual(df, rooms, periods) for _ in range(POP_SIZE)]

def select(population):
    population.sort(key=lambda x: fitness(x))
    return population[:20]

def crossover(p1, p2):
    point = random.randint(0, len(p1)-1)
    return p1[:point] + p2[point:]

def mutate(individual, rooms, periods):
    for i, gene in enumerate(individual):
        if random.random() < MUTATION_RATE:
            gene["day"] = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            gene["period"] = random.choice(periods)
            available_rooms = get_available_rooms(gene.get("students", 0), rooms)
            if available_rooms:
                room_entry = random.choice(available_rooms)
                gene["room"] = room_entry['id']
                gene["capacity"] = room_entry['capacity']
            individual[i] = gene
    return individual

def run_ga(df):
    rooms = load_rooms()
    timeslots = load_timeslots()

    if not rooms:
        raise Exception("No room data available in the database.")

    if timeslots:
        periods = sorted({slot['time'] for slot in timeslots if slot.get('time')})
        if not periods:
            periods = ["08:00-10:00", "10:00-12:00", "13:00-15:00", "15:00-17:00"]
    else:
        periods = ["08:00-10:00", "10:00-12:00", "13:00-15:00", "15:00-17:00"]

    population = create_population(df, rooms, periods)

    best_fitness_history = []
    stagnation_counter = 0
    last_best_fitness = float('inf')

    for generation in range(GENERATIONS):
        population = sorted(population, key=lambda x: fitness(x))
        current_best = fitness(population[0])
        best_fitness_history.append(current_best)

        if current_best == last_best_fitness:
            stagnation_counter += 1
        else:
            stagnation_counter = 0
            last_best_fitness = current_best

        current_mutation_rate = MUTATION_RATE
        if stagnation_counter > 20:
            current_mutation_rate = min(MUTATION_RATE * 2, 0.5)

        next_gen = population[:5]
        while len(next_gen) < POP_SIZE:
            parent1 = select(population)
            parent2 = select(population)
            child = crossover(parent1, parent2)
            child = mutate(child, rooms, periods)
            next_gen.append(child)

        population = next_gen

    best = min(population, key=lambda x: fitness(x))
    return best

# Exam GA functions
def get_available_exam_rooms(students, required_type=None, rooms=None):
    rooms = rooms if rooms is not None else load_rooms()
    available = [room for room in rooms if room['capacity'] >= students]
    if required_type:
        # Filter by room type if specified (this could be extended with room types)
        pass
    return available

def create_exam_individual(df, rooms, num_exam_periods):
    individual = []
    for _, row in df.iterrows():
        explicit_room = row.get("room")
        if has_value(explicit_room):
            room = str(explicit_room)
        else:
            available_rooms = get_available_exam_rooms(row.get("students", 0), row.get("required_room_type"), rooms=rooms)
            if available_rooms:
                room = random.choice(available_rooms)['id']
            else:
                room = None
        gene = (
            row.get("course"),
            row.get("lecturer"),
            room,
            random.randint(0, num_exam_periods - 1),
            row.get("group"),
            row.get("students", 0)
        )
        individual.append(gene)
    return individual


def create_exam_population(df, rooms, num_exam_periods):
    return [create_exam_individual(df, rooms, num_exam_periods) for _ in range(POP_SIZE)]


def ensure_exam_assignments(result, num_exam_periods):
    final = []
    for index, gene in enumerate(result):
        if not isinstance(gene, tuple) or len(gene) < 6:
            period_index = index % num_exam_periods
            final.append((
                gene[0] if len(gene) > 0 else None,
                gene[1] if len(gene) > 1 else None,
                gene[2] if len(gene) > 2 else None,
                period_index,
                gene[4] if len(gene) > 4 else None,
                gene[5] if len(gene) > 5 else 0
            ))
            continue

        period_index = gene[3]
        if not isinstance(period_index, int) or period_index < 0 or period_index >= num_exam_periods:
            period_index = index % num_exam_periods

        final.append((gene[0], gene[1], gene[2], period_index, gene[4], gene[5]))
    return final

def is_valid_assignment(course, timeslot_index, assignments):
    for assigned in assignments:
        if assigned["timeslot_index"] != timeslot_index:
            continue
        if course.get("room") and assigned.get("room") and course["room"] == assigned["room"]:
            return False
        if course.get("lecturer") and assigned.get("lecturer") and course["lecturer"] == assigned["lecturer"]:
            return False
    return True


def find_room_for_timeslot(course, timeslot_index, rooms, assignments):
    explicit_room = course.get("room")
    if has_value(explicit_room):
        if all(assigned["timeslot_index"] != timeslot_index or assigned.get("room") != explicit_room for assigned in assignments):
            return explicit_room

    available = get_available_exam_rooms(course.get("students", 0), None, rooms=rooms)
    for room in available:
        if all(assigned["timeslot_index"] != timeslot_index or assigned.get("room") != room["id"] for assigned in assignments):
            return room["id"]
    return explicit_room if has_value(explicit_room) else (available[0]["id"] if available else None)


def count_assignment_conflicts(course, timeslot_index, assignments):
    conflicts = 0
    for assigned in assignments:
        if assigned["timeslot_index"] != timeslot_index:
            continue
        if course.get("room") and assigned.get("room") and course["room"] == assigned["room"]:
            conflicts += 1
        if course.get("lecturer") and assigned.get("lecturer") and course["lecturer"] == assigned["lecturer"]:
            conflicts += 1
    return conflicts


def get_timeslot_indices_by_day(exam_periods):
    indices_by_day = {}
    for idx, period in enumerate(exam_periods):
        day = normalize_exam_day(period.get("day"))
        indices_by_day.setdefault(day, []).append(idx)
    return indices_by_day


def choose_least_conflicting_slot(course, exam_periods, rooms, assignments, preferred_day=None):
    best_index = None
    best_conflicts = float("inf")
    best_load = float("inf")

    def get_timeslot_load(index):
        return sum(1 for assigned in assignments if assigned["timeslot_index"] == index)

    def try_index(index):
        nonlocal best_index, best_conflicts, best_load
        conflicts = count_assignment_conflicts(course, index, assignments)
        load = get_timeslot_load(index)
        candidate = (conflicts, load, index)
        current = (best_conflicts, best_load, best_index if best_index is not None else float('inf'))
        if candidate < current:
            best_conflicts, best_load, best_index = conflicts, load, index

    if preferred_day is not None:
        day_indices = get_timeslot_indices_by_day(exam_periods).get(normalize_exam_day(preferred_day), [])
        for index in day_indices:
            try_index(index)
        if best_index is not None:
            room = find_room_for_timeslot(course, best_index, rooms, assignments)
            return {
                "course": course.get("course"),
                "lecturer": course.get("lecturer"),
                "room": room,
                "timeslot_index": best_index,
                "group": course.get("group"),
                "students": course.get("students", 0)
            }

    for index, _ in enumerate(exam_periods):
        try_index(index)

    room = find_room_for_timeslot(course, best_index, rooms, assignments)
    return {
        "course": course.get("course"),
        "lecturer": course.get("lecturer"),
        "room": room,
        "timeslot_index": best_index,
        "group": course.get("group"),
        "students": course.get("students", 0)
    }


def deterministic_exam_assignment(df, rooms, exam_periods):
    assignments = []
    timeslot_indices_by_day = get_timeslot_indices_by_day(exam_periods)

    for _, row in df.iterrows():
        requested_day = normalize_exam_day(row.get("day")) if row.get("day") is not None else "Day1"
        course = {
            "course": row.get("course"),
            "lecturer": row.get("lecturer"),
            "room": row.get("room"),
            "group": row.get("group"),
            "students": row.get("students", 0)
        }

        assigned = False
        valid_indices = [
            index for index in timeslot_indices_by_day.get(requested_day, [])
            if is_valid_assignment(course, index, assignments)
        ]

        if valid_indices:
            best_assignment = choose_least_conflicting_slot(course, exam_periods, rooms, assignments, preferred_day=requested_day)
            assignments.append(best_assignment)
            assigned = True

        if not assigned:
            fallback = choose_least_conflicting_slot(course, exam_periods, rooms, assignments, preferred_day=requested_day)
            assignments.append(fallback)

    return assignments

def mutate_exam(individual, rooms, num_exam_periods):
    if random.random() < MUTATION_RATE:
        i = random.randint(0, len(individual)-1)
        gene = list(individual[i])
        gene[3] = random.randint(0, num_exam_periods - 1)
        available_rooms = get_available_exam_rooms(gene[5], rooms=rooms)
        if available_rooms:
            gene[2] = random.choice(available_rooms)['id']
        individual[i] = tuple(gene)
    return individual

def run_exam_ga(df):
    rooms = load_rooms()

    if "day" not in df.columns:
        df["day"] = "Day1"
    else:
        df["day"] = df["day"].apply(normalize_exam_day)
        if df["day"].isna().all() or (df["day"].astype(str).str.strip() == "").all():
            df["day"] = "Day1"

    detected_days = sort_exam_days(df["day"].tolist())
    if not detected_days:
        detected_days = ["Day1"]

    db_exam_periods = get_exam_periods_data()
    if db_exam_periods:
        unique_days = sort_exam_days([ep["day"] for ep in db_exam_periods])
        exam_periods = get_exam_timeslots(unique_days)
        print("EXAM PERIODS LOADED FROM DATABASE DAYS:", unique_days)
        print("EXAM PERIODS USING FIXED TIMESLOTS:", exam_periods)
    else:
        exam_periods = get_exam_timeslots(detected_days)
        print("EXAM DETECTED DAYS (sorted):", detected_days)
        print("EXAM GENERATED PERIODS:", exam_periods)

    explicit_rooms = any(has_value(row.get("room")) for _, row in df.iterrows())
    if not rooms and not explicit_rooms:
        raise Exception("No room data available in the database and no explicit room assignments were provided in the uploaded exam file.")

    num_exam_periods = len(exam_periods)
    if num_exam_periods == 0:
        raise Exception("Fixed exam timeslots could not be loaded. Please check the schedule configuration.")

    assignments = deterministic_exam_assignment(df, rooms, exam_periods)
    print("EXAM TOTAL ASSIGNMENTS:", len(assignments))

    result = [
        (
            assignment["course"],
            assignment["lecturer"],
            assignment["room"],
            assignment["timeslot_index"],
            assignment["group"],
            assignment["students"]
        )
        for assignment in assignments
    ]

    result = sorted(result, key=lambda g: g[3])
    return result, exam_periods

def select_exam(population):
    population.sort(key=lambda x: exam_fitness(x))
    return population[:20]