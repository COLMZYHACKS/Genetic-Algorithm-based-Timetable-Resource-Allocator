import random
from services.fitness import fitness
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from services.database_service import get_rooms_data
from services.parser import normalize_exam_day, normalize_period_string, split_day_from_period

# GA PARAMETERS - BALANCED FOR PERFORMANCE
POP_SIZE = 80
GENERATIONS = 500
RESTARTS = 3
ELITE_SIZE = 8
TOURNAMENT_SIZE = 6
MUTATION_RATE = 0.15  # Reduced from 0.2 for stability

# TIMETABLE STRUCTURE
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
COURSE_TIMESLOTS = [
    "07:00-09:00",
    "09:00-11:00",
    "11:00-13:00",
    "13:30-15:30",
    "15:30-17:30",
    "17:30-19:30"
]


def get_course_timeslots():
    # The institution defines strict course periods and the GA must ignore any CSV time values.
    # The 13:00-13:30 break is excluded entirely from scheduling.
    return COURSE_TIMESLOTS.copy()


# 🧬 CREATE ONE TIMETABLE (INDIVIDUAL)

def normalize_room(room_value):
    if room_value is None:
        return None
    room_str = str(room_value).strip()
    return room_str if room_str else None


def get_available_rooms(students, rooms):
    return [room for room in rooms if room['capacity'] >= students]


def get_room_choices(row, rooms):
    explicit_room = normalize_room(row.get("room"))
    if explicit_room:
        return [explicit_room]

    available_rooms = get_available_rooms(row.get("students", 0), rooms)
    return [room['id'] for room in available_rooms]


def create_individual(df, rooms, periods):
    individual = []

    def has_value(value):
        if value is None:
            return False
        text = str(value).strip().lower()
        return text not in ("", "nan", "none")

    for _, row in df.iterrows():
        room_choices = get_room_choices(row, rooms)
        room = random.choice(room_choices) if room_choices else None

        day_value = row.get("day")
        period_value = row.get("period")

        if isinstance(period_value, str) and period_value.strip():
            from_day, normalized_period = split_day_from_period(period_value)
            if from_day:
                day_value = from_day
            period_value = normalize_period_string(normalized_period or period_value)

        day = day_value if day_value is not None and str(day_value).strip() else random.choice(DAYS)
        period = period_value if period_value is not None and str(period_value).strip() else random.choice(periods)

        gene = {
            "course": row.get("course"),
            "lecturer": row.get("lecturer"),
            "room": room,
            "day": day,
            "period": period,
            "group": row.get("group", "default"),
            "capacity": row.get("capacity", 100),
            "students": row.get("students", 50)
        }
        individual.append(gene)

    return individual


# 👥 INITIAL POPULATION
def create_population(df, rooms, periods):
    return [create_individual(df, rooms, periods) for _ in range(POP_SIZE)]


# 🧬 CROSSOVER (COMBINE TWO TIMETABLES)
def crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    child = parent1[:point] + parent2[point:]
    return child


# 🔁 MUTATION (SMART VERSION)
def mutate(individual, rooms, periods):
    for i, gene in enumerate(individual):
        if random.random() < MUTATION_RATE:
            # 70% chance to mutate time, 30% chance to mutate both
            if random.random() < 0.7:
                gene["day"] = random.choice(DAYS)
                gene["period"] = random.choice(periods)
            else:
                # Full reassignment for stuck solutions
                gene["day"] = random.choice(DAYS)
                gene["period"] = random.choice(periods)
                available_rooms = get_room_choices(gene, rooms)
                if available_rooms:
                    gene["room"] = random.choice(available_rooms)
    return individual

# 🔄 ADAPTIVE MUTATION
def mutate_adaptive(individual, mutation_rate, rooms, periods):
    for i, gene in enumerate(individual):
        if random.random() < mutation_rate:
            # Intelligent mutation based on problem constraints
            if random.random() < 0.6:
                # Time slot mutation
                gene["day"] = random.choice(DAYS)
                gene["period"] = random.choice(periods)
            elif random.random() < 0.8:
                # Room mutation
                available_rooms = get_room_choices(gene, rooms)
                if available_rooms:
                    gene["room"] = random.choice(available_rooms)
            else:
                # Full mutation for diversity
                gene["day"] = random.choice(DAYS)
                gene["period"] = random.choice(periods)
                available_rooms = get_room_choices(gene, rooms)
                if available_rooms:
                    gene["room"] = random.choice(available_rooms)
    return individual


def repair_individual(individual, periods):
    def build_bookings(ind):
        lecturer_bookings = {}
        room_bookings = {}
        group_bookings = {}
        for gene in ind:
            lecturer = gene.get("lecturer")
            room = gene.get("room")
            group = gene.get("group")
            day = gene.get("day")
            period = gene.get("period")
            if lecturer:
                lecturer_bookings[(lecturer, day, period)] = lecturer_bookings.get((lecturer, day, period), 0) + 1
            if room:
                room_bookings[(room, day, period)] = room_bookings.get((room, day, period), 0) + 1
            if group:
                group_bookings[(group, day, period)] = group_bookings.get((group, day, period), 0) + 1
        return lecturer_bookings, room_bookings, group_bookings

    def has_conflict(gene, bookings):
        lecturer, room, group, day, period = gene.get("lecturer"), gene.get("room"), gene.get("group"), gene.get("day"), gene.get("period")
        if lecturer and bookings[0].get((lecturer, day, period), 0) > 1:
            return True
        if room and bookings[1].get((room, day, period), 0) > 1:
            return True
        if group and bookings[2].get((group, day, period), 0) > 1:
            return True
        return False

    fixed = [dict(gene) for gene in individual]
    bookings = build_bookings(fixed)

    for _ in range(3):
        moved = False
        for gene in fixed:
            if not has_conflict(gene, bookings):
                continue
            current_keys = {
                "lecturer": (gene.get("lecturer"), gene.get("day"), gene.get("period")),
                "room": (gene.get("room"), gene.get("day"), gene.get("period")),
                "group": (gene.get("group"), gene.get("day"), gene.get("period"))
            }
            for day in DAYS:
                if moved:
                    break
                for period in periods:
                    if day == gene.get("day") and period == gene.get("period"):
                        continue
                    conflict = False
                    if gene.get("lecturer") and bookings[0].get((gene["lecturer"], day, period), 0) > 0:
                        conflict = True
                    if gene.get("room") and bookings[1].get((gene["room"], day, period), 0) > 0:
                        conflict = True
                    if gene.get("group") and bookings[2].get((gene["group"], day, period), 0) > 0:
                        conflict = True
                    if conflict:
                        continue
                    # Move gene to a clean slot
                    for key, value in current_keys.items():
                        if value[0] is None:
                            continue
                        if key == "lecturer":
                            bookings[0][value] -= 1
                        elif key == "room":
                            bookings[1][value] -= 1
                        elif key == "group":
                            bookings[2][value] -= 1
                    gene["day"] = day
                    gene["period"] = period
                    bookings[0][(gene.get("lecturer"), day, period)] = bookings[0].get((gene.get("lecturer"), day, period), 0) + 1
                    bookings[1][(gene.get("room"), day, period)] = bookings[1].get((gene.get("room"), day, period), 0) + 1
                    bookings[2][(gene.get("group"), day, period)] = bookings[2].get((gene.get("group"), day, period), 0) + 1
                    moved = True
                    break
        if not moved:
            break
    return fixed


# 🏆 TOURNAMENT SELECTION (BETTER THAN RANDOM)
def select(population):
    tournament = random.sample(population, TOURNAMENT_SIZE)
    return min(tournament, key=lambda x: fitness(x))


# 🚀 MAIN GA LOOP - ENHANCED
def run_ga(df):
    if df is None or getattr(df, 'empty', False):
        raise ValueError("No timetable data available for generation. Please upload a file or enable database data with populated courses.")

    # Load data within app context
    try:
        rooms = get_rooms_data()

        if not rooms and "room" not in df.columns:
            raise ValueError("No rooms found in database and uploaded file does not include room assignments. Please add rooms in Data Management or provide room data in the upload.")

        periods = get_course_timeslots()
        if not periods:
            raise ValueError("Fixed course timeslots could not be loaded. Please check the schedule configuration.")

    except Exception as e:
        raise Exception(f"Failed to load essential data: {str(e)}")

    best_solution = None
    best_solution_fitness = float('inf')

    # Create a single executor for the whole GA run to avoid repeated worker spawn overhead on Windows
    executor = None
    try:
        max_workers = min(4, max(1, multiprocessing.cpu_count() - 1))
        executor = ProcessPoolExecutor(max_workers=max_workers)
    except Exception:
        executor = None

    for attempt in range(RESTARTS):
        population = create_population(df, rooms, periods)
        best_fitness_history = []
        stagnation_counter = 0
        last_best_fitness = float('inf')

        for generation in range(GENERATIONS):
            # Evaluate fitness in parallel (fast path), fallback to serial if unavailable
            try:
                if executor is not None:
                    fitness_values = list(executor.map(fitness, population))
                else:
                    fitness_values = [fitness(ind) for ind in population]
            except Exception:
                fitness_values = [fitness(ind) for ind in population]

            # Pair and sort by fitness value (lower is better)
            paired = list(zip(population, fitness_values))
            paired.sort(key=lambda p: p[1])
            population = [p for p, _ in paired]
            fitness_values = [f for _, f in paired]
            current_best = fitness_values[0]
            best_fitness_history.append(current_best)

            # Adaptive mutation and stagnation detection
            if current_best == last_best_fitness:
                stagnation_counter += 1
            else:
                stagnation_counter = 0
                last_best_fitness = current_best

            # If stagnated for 20 generations, increase mutation rate temporarily
            current_mutation_rate = MUTATION_RATE
            if stagnation_counter > 20:
                current_mutation_rate = min(MUTATION_RATE * 2, 0.5)  # Cap at 50%

            # Elitism (keep best solutions)
            next_gen = population[:ELITE_SIZE]

            # Tournament selection using computed fitness_values to avoid re-evaluation
            def select_index(pop_size, fitness_vals):
                inds = random.sample(range(pop_size), TOURNAMENT_SIZE)
                return min(inds, key=lambda i: fitness_vals[i])

            # Generate rest of population
            while len(next_gen) < POP_SIZE:
                idx1 = select_index(len(population), fitness_values)
                idx2 = select_index(len(population), fitness_values)
                parent1 = population[idx1]
                parent2 = population[idx2]

                child = crossover(parent1, parent2)
                child = mutate_adaptive(child, current_mutation_rate, rooms, periods)

                next_gen.append(child)

            population = next_gen

            # Progress reporting
            progress_percent = int((generation + 1) / GENERATIONS * 100)
            if generation % 5 == 0 or generation == GENERATIONS - 1:
                print(f"PROGRESS:{progress_percent}% | Gen {generation + 1}/{GENERATIONS} | Fitness: {current_best:.2f}")

        # Final evaluation of the chosen candidates
        try:
            if executor is not None:
                final_fitnesses = list(executor.map(fitness, population))
            else:
                final_fitnesses = [fitness(ind) for ind in population]
        except Exception:
            final_fitnesses = [fitness(ind) for ind in population]

        best_idx = int(min(range(len(population)), key=lambda i: final_fitnesses[i]))
        candidate = population[best_idx]
        candidate = repair_individual(candidate, periods)
        candidate_fitness = fitness(candidate)
        print(f"ATTEMPT {attempt + 1}/{RESTARTS} best fitness: {candidate_fitness}")
        if candidate_fitness < best_solution_fitness:
            best_solution_fitness = candidate_fitness
            best_solution = candidate

    # Clean up executor
    try:
        if executor is not None:
            executor.shutdown(wait=True)
    except Exception:
        pass

    if best_solution is None:
        raise Exception("GA failed to produce a schedule")

    print(f"\nGA completed after {RESTARTS} restart(s). Best fitness: {best_solution_fitness}")
    return best_solution