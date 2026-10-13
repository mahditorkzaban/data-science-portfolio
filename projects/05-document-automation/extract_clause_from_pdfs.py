# -*- coding: utf-8 -*-

import fitz  
import re
import os
import pandas as pd

def extract_text_from_page(pdf_path, page_number):
    text = "Bulletin de notes"
    with fitz.open(pdf_path) as pdf:
        if len(pdf) > page_number:
            page = pdf[page_number]
            text = page.get_text()
    return text

def find_phrase_in_text(text, phrase):
    escaped_phrase = re.escape(phrase)
    pattern = rf'({escaped_phrase}.*?)(?=\b(19|20)\d{2}\b|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def process_pdfs(directory, phrase):
    data = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            text = extract_text_from_page(file_path, 4)  # Page 5 is index 4
            extracted_text = find_phrase_in_text(text, phrase)
            person_name = filename.rsplit('.', 1)[0]  # Assuming the file name is the person's name
            data.append({"Person": person_name, "ExtractedText": extracted_text})
    return data

def save_to_csv(data, output_path):
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)

pdf_directory = "pdfs"
output_csv = 'extracted_clauses.csv'
search_phrase = "3-1 : Durée du stage"

data = process_pdfs(pdf_directory, search_phrase)
save_to_csv(data, output_csv)

print(f"Data has been saved to {output_csv}")
