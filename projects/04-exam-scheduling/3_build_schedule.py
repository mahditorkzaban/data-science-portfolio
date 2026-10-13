import os
import pandas as pd
path = "data"  # folder holding the input / output workbooks
input_file_path = os.path.join(path, 'Subgrouped_Exams.xlsx')
output_file_path = os.path.join(path, 'Rattrapage Schedule.xlsx')
data = pd.read_excel(input_file_path)
grouped_data = data.groupby(['duration_group', 'Subgroup']).agg({
    'Subjects': list,
    'id': list,
    'student_count':list,
    'duration_group': list  ,
})
grouped_data['subject_count'] = grouped_data['Subjects'].apply(len)
grouped_data['total_number_of_students'] = grouped_data['student_count'].apply(lambda x: sum(x))
grouped_data
grouped_data.to_excel(output_file_path, index = False)