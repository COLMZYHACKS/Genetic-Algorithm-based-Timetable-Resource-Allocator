import sys
sys.path.append('c:/Users/malco/Downloads/timetable_ai/backend')
from services.parser import parse_file
df = parse_file('c:/Users/malco/Downloads/timetable_ai/test_upload.csv')
print('Columns:', df.columns.tolist())
print(df.head())