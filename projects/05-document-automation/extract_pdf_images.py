"""Extract every embedded image from a PDF and zip them. Needs: pip install PyMuPDF"""
import fitz  # PyMuPDF
import os

def extract_images_from_pdf(pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"page{page_num+1}_img{img_index+1}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)

            with open(image_path, "wb") as f:
                f.write(image_bytes)
                image_count += 1

    print(f"✅ Extracted {image_count} images to '{output_folder}'")


pdf_file_path = "input.pdf"
output_folder_path = "extracted_images"
extract_images_from_pdf(pdf_file_path, output_folder_path)


import zipfile

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

    print(f"✅ Folder '{folder_path}' compressed into '{zip_path}'")


zip_file_path = "extracted_images.zip"
zip_folder(output_folder_path, zip_file_path)

