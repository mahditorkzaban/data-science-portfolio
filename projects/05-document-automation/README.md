# Document Automation Toolkit

Small, single-purpose scripts that automate repetitive admin work with PDFs, Word files and e-mail.

| Script | Does | Needs |
|---|---|---|
| `ocr_split_pdf_by_section.py` | Splits a large scanned PDF into one file per person by **OCR-detecting a heading** on each page | PyMuPDF, Tesseract, PyPDF2 |
| `extract_clause_from_pdfs.py` | Pulls one clause (e.g. internship duration) out of a folder of PDFs into a CSV with regex | PyMuPDF, pandas |
| `split_pdf_every_n_pages.py` | Cuts a PDF into fixed-size parts | PyPDF2 |
| `pdf_to_jpeg.py` | Batch-converts PDFs to 300-dpi JPEGs | pdf2image, Poppler |
| `extract_pdf_images.py` | Extracts all embedded images from a PDF and zips them | PyMuPDF |
| `docx_to_pdf.py` | Batch Word → PDF | docx2pdf |
| `run_word_macros_on_folder.py` | Runs VBA macros over every `.docx` in a folder | Windows, MS Word, pywin32 |
| `bulk_email_from_excel.py` | Sends one personalised e-mail per spreadsheet row, with CC, throttling and automatic reconnect | pandas, SMTP |

## Highlights

- **OCR section splitter**: renders each page at 300 dpi, runs Tesseract, finds the page where a phrase appears, and cuts the PDF between consecutive matches.
- **Bulk mailer**: credentials come from environment variables, never from code.

```bash
export SMTP_SERVER=smtp.example.com SMTP_USER=me@example.com SMTP_PASSWORD='...'
python bulk_email_from_excel.py
```

Paths in the scripts are placeholders (`input.pdf`, `pdfs/`, `docs/`); edit them at the bottom of each file.
