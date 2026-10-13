"""Open every .docx in a folder, run two VBA macros on each, save and close (Windows + MS Word)."""
import os
import win32com.client as win32

# Path to the folder containing the Word files
folder_path = r"docs"  

# Initialize Word application
word_app = win32.Dispatch("Word.Application")
word_app.Visible = True

# Loop through all files in the specified folder
for filename in os.listdir(folder_path):
    if filename.endswith(".docx"):
        file_path = os.path.join(folder_path, filename)
        
        # Open the Word document
        doc = word_app.Documents.Open(file_path)
        
        
        try:
            word_app.Run("Macro1")  
        except Exception as e:
            print(f"Error running Macro1 on {filename}: {e}")
        
        # Run the second macro
        try:
            word_app.Run("Macro2")
        except Exception as e:
            print(f"Error running Macro2 on {filename}: {e}")
        
        # Save and close the document
        doc.Save()
        doc.Close()

# Quit the Word application
word_app.Quit()
