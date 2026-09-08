from services.constraint_service import check_hard_constraints, check_exam_hard_constraints
from services.time_utils import parse_time_value

def fitness(individual):
    penalty = 0

    # HARD constraints
    penalty += check_hard_constraints(individual)

    # SOFT constraints
    for gene in individual:
        _, _, room, period, _, _, room_capacity, students = gene

        # Parse start time to avoid late classes
        try:
            _, time_part = period.split(' ', 1)
            start_str, _ = time_part.split('-')
            start_min = parse_time_value(start_str)
            if start_min and start_min > 17 * 60:  # After 5 PM
                penalty += 5
        except:
            pass

        # Capacity overflow penalty
        if room is not None and students > room_capacity:
            penalty += 20

        # Prefer assigned rooms when possible
        if room is None:
            penalty += 10

    return penalty


def exam_fitness(individual):
    penalty = 0

    # HARD constraints for exams
    penalty += check_exam_hard_constraints(individual)

    # SOFT constraints for exams
    for gene in individual:
        _, _, _, exam_period, _, _ = gene

        # Prefer earlier exam periods
        if isinstance(exam_period, int) and exam_period > 1:
            penalty += 1

    return penalty