#pdf_converter
import PyPDF2
import json

def pdf_to_text(pdf_path):
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Если текст пустой, это можно считать ошибкой
        if not text.strip():
            raise ValueError("Не удалось извлечь текст из PDF.")
        
        return text
    
    except Exception as e:
        # Возвращаем ошибку в формате JSON
        error_result = {
            "status": "error",
            "error_message": str(e)
        }
        return json.dumps(error_result)
