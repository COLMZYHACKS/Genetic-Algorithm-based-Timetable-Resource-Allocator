import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path('backend').resolve()))

from services.parser import normalize_exam_day, parse_file
from services.ga_engine import sort_exam_days
from services.fitness import fitness


class TestParserAndFitness(unittest.TestCase):
    def test_normalize_exam_day_abbreviation(self):
        self.assertEqual(normalize_exam_day('Fri'), 'Friday')
        self.assertEqual(normalize_exam_day('FRI'), 'Friday')
        self.assertEqual(normalize_exam_day('fri.'), 'Friday')
        self.assertEqual(normalize_exam_day('Day 1'), 'Day1')
        self.assertEqual(normalize_exam_day('1'), 'Day1')

    def test_sort_exam_days_uses_canonical_order(self):
        self.assertEqual(
            sort_exam_days(['Tuesday', 'Fri', 'Monday', 'Thursday']),
            ['Monday', 'Tuesday', 'Thursday', 'Friday']
        )

    def test_parse_file_preserves_period_and_group_synonyms(self):
        csv_content = """day,classroom,slot,start_time,end_time,course_full,course_abbrev,course_code,level,lecturer,is_practical,class_size,room_size,StudentGroup
Monday,LH 1,1,07:00,08:00,GL 1A 159 (P),GL,159,100,ANOHAH,TRUE,120,250,CS100
"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp:
            temp.write(csv_content)
            temp.flush()
            df = parse_file(temp.name)

        self.assertIn('period', df.columns)
        self.assertIn('group', df.columns)
        self.assertEqual(df.loc[0, 'period'], '1')
        self.assertEqual(df.loc[0, 'group'], 'CS100')

    def test_fitness_penalties(self):
        individual = [
            {
                'course': 'CS101',
                'lecturer': 'Dr. Smith',
                'room': 'R1',
                'day': 'Monday',
                'period': '07:00-09:00',
                'group': 'G1',
                'capacity': 30,
                'students': 40
            },
            {
                'course': 'CS102',
                'lecturer': 'Dr. Smith',
                'room': 'R1',
                'day': 'Monday',
                'period': '07:00-09:00',
                'group': 'G1',
                'capacity': 30,
                'students': 20
            },
            {
                'course': 'CS103',
                'lecturer': 'Dr. Jones',
                'room': None,
                'day': 'Tuesday',
                'period': '09:00-11:00',
                'group': 'G2',
                'capacity': 30,
                'students': 25
            }
        ]
        self.assertEqual(fitness(individual), 1520)


if __name__ == '__main__':
    unittest.main()
