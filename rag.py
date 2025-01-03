from openai import OpenAI
import PyPDF2
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:8501"])
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-default-secret-key')

client = OpenAI(
    api_key= os.getenv('DEEPSEEK_API_TOKEN', 'your-default-secret-key'),
    base_url="https://api.deepseek.com/beta",
)

# Create a temporary directory to store PDF text
TEMP_DIR = tempfile.gettempdir()
PDF_TEXT_PATH = os.path.join(TEMP_DIR, 'pdf_text.txt')

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = []
        
        # Extract text page by page with better formatting
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            # Add page number for context
            text.append(f"\nPage {page_num + 1}:\n{page.extract_text().strip()}")
        
        # Join all pages with clear separation
        return "\n".join(text)
    except Exception as e:
        print(f"Error in PDF extraction: {str(e)}")
        raise

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400

    pdf_file = request.files['pdf']
    
    if pdf_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    try:
        # Extract text from the uploaded PDF
        extracted_text = extract_text_from_pdf(pdf_file)
        
        if not extracted_text.strip():
            return jsonify({'error': 'No text could be extracted from the PDF'}), 400
        
        # Store text in a temporary file
        with open(PDF_TEXT_PATH, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        # Return first 100 characters of extracted text for verification
        preview = extracted_text[:100] + "..."
        return jsonify({
            'message': 'PDF uploaded and processed successfully',
            'preview': preview
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    if not os.path.exists(PDF_TEXT_PATH):
        return jsonify({'error': 'No PDF has been uploaded yet'}), 400

    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        
        # Read the stored PDF text
        with open(PDF_TEXT_PATH, 'r', encoding='utf-8') as f:
            context = f.read()

        if not context.strip():
            return jsonify({'error': 'The PDF content appears to be empty'}), 400

        # Improved prompt engineering
        prompt = (
            "You are a helpful AI assistant tasked with answering questions about a document. "
            "Below is the content of the document, followed by a question. "
            "Please follow these rules:\n"
            "1. Answer only based on the information in the document\n"
            "2. If you can't find the exact information, but can make a reasonable inference from the content, start your answer with 'Based on the document...'\n"
            "3. If the information is not in the document, say 'I cannot find this information in the document.'\n"
            "4. Include page numbers in your answer when possible\n\n"
            f"Document Content:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer: "
        )

        response = client.completions.create(
            model="deepseek-chat",
            prompt=prompt,
            temperature=0.3,  # Reduced temperature for more focused answers
            max_tokens=1000,  # Increased max tokens
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )

        # Extract and clean the answer
        answer = response.choices[0].text.strip() if response.choices else "No answer generated"
        
        # Log for debugging
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        
        return jsonify({'answer': answer}), 200
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")  # Debug logging
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
