import pandas as pd
from services.ga import run_ga, fitness
from app import app

# Test with optimal sample data
def main():
	print('Testing GA with optimal data format...')
	df = pd.read_csv('../sample_optimal_timetable.csv')
	print(f'Dataset: {len(df)} courses')
	print(f'Unique lecturers: {df["lecturer"].nunique()}')
	print(f'Unique groups: {df["group"].nunique()}')
	print(f'Unique rooms: {df["room"].nunique()}')
	print(f'Average class size: {df["students"].mean():.1f} students')
	print(f'Capacity utilization: {(df["students"] / df["capacity"]).mean():.1%}')

	import time
	print('\nRunning GA...')
	start = time.time()
	with app.app_context():
		result = run_ga(df)
		final_fitness = fitness(result)
	elapsed = time.time() - start
	print(f'Final fitness: {final_fitness}')
	print('GA completed successfully!')
	print(f'ElapsedSeconds: {elapsed:.3f}')


if __name__ == '__main__':
	main()