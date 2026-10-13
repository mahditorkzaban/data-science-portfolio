import os
from docx2pdf import convert

# Path to the directory containing Word files
word_dir = "docs"

# Iterate through the directory to find .docx files
for file_name in os.listdir(word_dir):
    if file_name.endswith(".docx"):
        word_file = os.path.join(word_dir, file_name)
        convert(word_file)
