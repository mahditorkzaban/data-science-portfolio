import pandas as pd
import os
def detect_overlaps(exams_grouped):
    exams_grouped['subgroup'] = 0
    subgroup_id = 1 
    for index, row in exams_grouped.iterrows():
        if row['subgroup'] == 0:  # If no subgroup assigned
            current_ids = set(row['id'])
            exams_grouped.at[index, 'subgroup'] = subgroup_id
            # Check for overlaps with other exams
            for idx, other_row in exams_grouped.iterrows():
                if other_row['subgroup'] == 0:  # Only consider ungrouped exams
                    other_ids = set(other_row['id'])
                    if current_ids & other_ids:  # If there's an overlap in IDs
                        exams_grouped.at[idx, 'subgroup'] = subgroup_id
            subgroup_id += 1
path = "data"  # folder holding the input / output workbooks
input_file_path = os.path.join(path, 'final.xlsx')
output_file_path = os.path.join(path, 'Sorted_Exams.xlsx')
exam_sheet = pd.read_excel(input_file_path, sheet_name='exam')
room_sheet = pd.read_excel(input_file_path, sheet_name='room')
exam_sheet['duration'] = exam_sheet['duration'].astype(int)
exam_sheet['duration'] = pd.to_timedelta(exam_sheet['duration'], unit='minutes')
exams_grouped = exam_sheet.groupby('Subjects').agg({'id': lambda ids: list(ids), 'duration': 'first'}).reset_index()
exams_grouped['student_count'] = exams_grouped['id'].apply(len)
exams_grouped = exams_grouped.sort_values(by='student_count', ascending=False)
exams_grouped = exams_grouped.sort_values(by='duration', ascending=True)
bins = [pd.Timedelta(minutes=0), pd.Timedelta(minutes=60), pd.Timedelta(minutes=120), 
        pd.Timedelta(minutes=180), pd.Timedelta.max]
labels = ['60', '120', '180', '180+']
exams_grouped['duration_group'] = pd.cut(exams_grouped['duration'].dt.total_seconds()/60, 
                                         bins=[0, 60, 120, 180, float('inf')], 
                                         labels=labels, right=False)
print(exams_grouped)
print("\nRoom Sheet:")
print(room_sheet.head())
exams_grouped.to_excel(output_file_path, index = False)