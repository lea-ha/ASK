import openai
import json
import os
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
    
    def analyze_text(self, text):
        """Analyze text and return summary, keywords, and questions"""
        prompt = """
        Analyze the following academic text and provide:
        1. A concise summary (2-3 sentences)
        2. Key terms and concepts (5-8 keywords)
        3. Study questions that test understanding (4-6 questions)
        
        Provide your response in JSON format with 'summary', 'keywords', and 'questions' fields.
        Make questions varied in difficulty and type (factual, analytical, application-based).
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Text to analyze:\n\n{text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "summary": result.get("summary", "No summary available"),
                "keywords": result.get("keywords", []),
                "questions": result.get("questions", [])
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._fallback_analysis(text)
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            raise Exception(f"Failed to analyze text: {str(e)}")
    
    def _fallback_analysis(self, text):
        """Fallback method if JSON parsing fails"""
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f"Summarize this text in 2-3 sentences: {text[:2000]}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            summary = response.choices[0].message.content
            return {
                "summary": summary,
                "keywords": ["analysis", "document", "content"],
                "questions": ["What are the main concepts in this document?"]
            }
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {
                "summary": "Document analysis unavailable",
                "keywords": [],
                "questions": []
            }