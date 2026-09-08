from services.fitness import fitness, get_fitness_breakdown

# Helper to create simple gene dicts
def gene(course, lecturer, room, day, period, group, capacity=50, students=30):
    return {
        'course': course,
        'lecturer': lecturer,
        'room': room,
        'day': day,
        'period': period,
        'group': group,
        'capacity': capacity,
        'students': students
    }


def run_tests():
    # TEST 1: Perfect timetable - no conflicts
    ind1 = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1'),
        gene('C2','L2','R2','Mon','09:00-11:00','G2'),
    ]
    f1 = fitness(ind1)
    bd1 = get_fitness_breakdown(ind1)
    print('Test1 fitness:', f1, bd1)

    # TEST 2: One lecturer conflict
    ind2 = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1'),
        gene('C2','L1','R2','Mon','07:00-09:00','G2'),
    ]
    f2 = fitness(ind2)
    print('Test2 fitness:', f2, get_fitness_breakdown(ind2))
    assert f2 > f1

    # TEST 3: Multiple lecturer conflicts
    ind3 = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1'),
        gene('C2','L1','R2','Mon','07:00-09:00','G2'),
        gene('C3','L1','R3','Mon','07:00-09:00','G3'),
    ]
    f3 = fitness(ind3)
    print('Test3 fitness:', f3, get_fitness_breakdown(ind3))
    assert f3 > f2

    # TEST 4: Room conflict
    ind4 = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1'),
        gene('C2','L2','R1','Mon','07:00-09:00','G2'),
    ]
    f4 = fitness(ind4)
    print('Test4 fitness:', f4, get_fitness_breakdown(ind4))
    assert f4 > f1

    # TEST 5: Capacity violation
    ind5 = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1', capacity=30, students=50),
        gene('C2','L2','R2','Mon','09:00-11:00','G2'),
    ]
    f5 = fitness(ind5)
    print('Test5 fitness:', f5, get_fitness_breakdown(ind5))
    assert f5 > f1

    # TEST 6: Several hard violations
    ind6 = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1', capacity=20, students=50),
        gene('C2','L1','R1','Mon','07:00-09:00','G1', capacity=20, students=50),
    ]
    f6 = fitness(ind6)
    print('Test6 fitness:', f6, get_fitness_breakdown(ind6))
    assert f6 > max(f2,f4,f5)

    # TEST 7: Same hard violations, different soft quality
    ind7a = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1'),
        gene('C2','L2','R2','Mon','19:30-21:30','G2'),
    ]
    ind7b = [
        gene('C1','L1','R1','Mon','07:00-09:00','G1'),
        gene('C2','L2','R2','Mon','09:00-11:00','G2'),
    ]
    f7a = fitness(ind7a)
    f7b = fitness(ind7b)
    print('Test7 fitness a/b:', f7a, f7b, get_fitness_breakdown(ind7a), get_fitness_breakdown(ind7b))
    # both have zero hard conflicts; soft quality should prefer earlier class
    assert f7b <= f7a

    # TEST 8: Invalid/empty timetable
    ind8 = []
    f8 = fitness(ind8)
    print('Test8 fitness (empty):', f8, get_fitness_breakdown(ind8))
    assert f8 > f1

    print('\nAll fitness tests passed.')

if __name__ == '__main__':
    run_tests()
