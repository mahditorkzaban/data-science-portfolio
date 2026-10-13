from PyPDF2 import PdfReader, PdfWriter

def split_pdf_every_four_pages(pdf_path):
    pdf_reader = PdfReader(pdf_path)
    total_pages = len(pdf_reader.pages)
    
    for i in range(0, total_pages, 4):
        pdf_writer = PdfWriter()
        end_page = min(i + 4, total_pages)  # Ensure we do not go beyond the last page
        
        for page_num in range(i, end_page):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        output_filename = f"{pdf_path[:-4]}_part_{i//4 + 1}.pdf"  # Save as part_1, part_2, ...
        with open(output_filename, "wb") as output_pdf:
            pdf_writer.write(output_pdf)
        print(f"Created: {output_filename}")

if __name__ == "__main__":
    pdf_path = 'input.pdf' 
    split_pdf_every_four_pages(pdf_path)
