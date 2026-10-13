import fitz
from PyPDF2 import PdfReader, PdfWriter
import pytesseract
from PIL import Image
import io

# Ensure Tesseract is installed and configured correctly
# Windows only: point to your Tesseract install if it is not on PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_with_ocr(pdf_path, page_number):
    """Extract text from a PDF page using OCR."""
    document = fitz.open(pdf_path)
    page = document[page_number]
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img)
    return text

def find_sections_with_ocr(pdf_path, phrase):
    """Find sections in a PDF where a specific phrase is found using OCR."""
    document = fitz.open(pdf_path)
    sections = []
    for i in range(len(document)):
        text = extract_text_with_ocr(pdf_path, i)
        if phrase in text:
            # Extract the first line of text as the section name
            lines = text.splitlines()
            if lines:  # Check if any text is present
                section_name = lines[0].strip()
                sections.append((i, section_name))
    return sections

def split_pdf_by_sections(pdf_path, sections):
    """Split a PDF into smaller PDFs based on identified sections."""
    pdf_reader = PdfReader(pdf_path)
    for index, (page_number, name) in enumerate(sections):
        start_page = page_number
        end_page = sections[index + 1][0] if (index + 1) < len(sections) else len(pdf_reader.pages)
        pdf_writer = PdfWriter()
        for page_num in range(start_page, end_page):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        # Sanitize the name to ensure it's a valid filename
        formatted_name = "".join(x for x in name if x.isalnum() or x in " _-").strip()
        output_pdf_path = f"{formatted_name}.pdf"
        with open(output_pdf_path, 'wb') as f:
            pdf_writer.write(f)
        print(f"Generated: {output_pdf_path}")

if __name__ == "__main__":
    pdf_path = "input.pdf"
    phrase = "Bulletin de notes"  # Or "Grade Transcript"
    sections = find_sections_with_ocr(pdf_path, phrase)
    if sections:
        split_pdf_by_sections(pdf_path, sections)
    else:
        print("No sections found with the specified phrase.")
