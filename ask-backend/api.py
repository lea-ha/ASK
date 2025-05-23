from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import logging
from io import BytesIO
import PyPDF2
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    logger.info("Health endpoint called...")
    return jsonify({"status": "ok"}), 200

@app.route('/api/analyze', methods=['POST'])
def analyze():
    logger.info("Analyze endpoint called...")
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    prompt = f"""
    Analyze the following text and provide the following information:
    1. Summary of the text
    2. The keywords in the text
    Provide your response in JSON format with 'summary' and 'keywords' fields.
    The keywords should be an array of strings."
    """
    try:
        # Analyze the text
        analysis = analyze_text(text)  
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        return jsonify({"error": "Failed to analyze text", "details": str(e)}), 500

# @app.route('/api/analyze_pdf', methods=['POST'])
# def analyze_pdf():
#     logger.info("Analyze PDF endpoint called...")
#     data = request.json
#     pdf_url = data.get('pdf_url')
    
#     if not pdf_url:
#         return jsonify({"error": "PDF URL is required"}), 400
    
#     try:
#         # Download the PDF
#         response = requests.get(pdf_url)
#         response.raise_for_status()
#         pdf_data = BytesIO(response.content)

#         # Use PyPDF2 to extract text from the PDF
#         pdf_reader = PyPDF2.PdfReader(pdf_data)
#         text = ""
#         for page in pdf_reader.pages:
#             text += page.extract_text()
        
#         # Analyze the text
#         analysis = analyze_text(text)
        
#         return jsonify(analysis), 200
    
#     except Exception as e:
#         logger.error(f"Error processing PDF: {e}")
#         return jsonify({"error": "Failed to process PDF", "details": str(e)}), 500

@app.route('/api/analyze_pdf', methods=['POST'])
def analyze_pdf():
    logger.info("Analyze PDF endpoint called (file upload)...")

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        pdf_data = BytesIO(file.read())
        text = extract_text_from_pdf(pdf_data)

        analysis = analyze_text(text)
        return jsonify(analysis), 200

    except Exception as e:
        logger.error(f"Error processing uploaded PDF: {e}")
        return jsonify({"error": "Failed to process PDF", "details": str(e)}), 500


def analyze_text(text):
    prompt = f"""
    Analyze the following text and provide the following information:
    1. Summary of the text
    2. The keywords in the text
    3. Generate a list of questions that are relevant to the text
    Provide your response in JSON format with 'summary' and 'keywords' and 'questions' fields.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            seed=42
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "summary": result.get("summary", "No summary available"),
            "keywords": result.get("keywords", []),
            "questions": result.get("questions", [])
        }
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        return {"error": "Failed to analyze text", "details": str(e)}
    
def extract_text_from_pdf(pdf_data):
    pdf_reader = PyPDF2.PdfReader(pdf_data)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

if __name__ == '__main__':
    app.run(debug=True)

