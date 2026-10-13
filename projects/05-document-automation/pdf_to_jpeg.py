from pdf2image import convert_from_path
import os

def pdfs_to_jpegs(pdf_folder, poppler_path, dpi=300):
    # Ensure the folder exists
    if not os.path.exists(pdf_folder):
        print("❌ The specified PDF folder does not exist.")
        return

    # Get a list of all PDF files in the folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("❌ No PDF files found in the folder.")
        return

    print(f"🔍 Found {len(pdf_files)} PDF files. Processing...")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"📄 Processing: {pdf_file}")

        # Convert PDF to images
        try:
            images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)

            # Save each page as a JPEG
            for i, img in enumerate(images):
                output_filename = f"{os.path.splitext(pdf_file)[0]}_page_{i+1}.jpg"
                img_path = os.path.join(pdf_folder, output_filename)
                img.save(img_path, "JPEG")
                print(f"✅ Saved: {output_filename}")

        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")

    print("🎉 All PDFs converted successfully!")

# Folder Paths
pdf_folder = "pdfs"  # folder containing the PDFs
poppler_path = None  # on Windows: path to poppler\\Library\\bin

# Convert all PDFs in the folder
pdfs_to_jpegs(pdf_folder, poppler_path)
