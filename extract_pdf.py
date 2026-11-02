import sys
try:
    import PyPDF2
    pdf_path = "/workspace/user_input_files/free-email-security-apis-guide-please use.pdf"
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    with open("/workspace/user_input_files/free-email-security-apis-guide.txt", 'w') as f:
        f.write(text)
    print("PDF extracted successfully")
except ImportError:
    print("PyPDF2 not installed, trying pdfplumber")
    try:
        import pdfplumber
        pdf_path = "/workspace/user_input_files/free-email-security-apis-guide-please use.pdf"
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        with open("/workspace/user_input_files/free-email-security-apis-guide.txt", 'w') as f:
            f.write(text)
        print("PDF extracted successfully with pdfplumber")
    except Exception as e:
        print(f"Error: {e}")
