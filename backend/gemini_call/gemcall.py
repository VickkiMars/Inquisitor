from google import genai
from google.genai import types
from google.api_core import retry
from ast import literal_eval
from dotenv import load_dotenv
import os
from backend.log_helper.report import log_message
from backend.pipeline.helper import get_content_between_curly_braces
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

is_retriable = lambda e: (isinstance(e, genai.errors.APIError) and e.code in {429, 503})

if not hasattr(genai.models.Models.generate_content, '__wrapped__'):
    genai.models.Models.generate_content = retry.Retry(
        predicate=is_retriable,
    )(genai.models.Models.generate_content)

config = types.GenerateContentConfig(temperature=0.0)
client = genai.Client(api_key=api_key)
chat = client.chats.create(model='gemini-2.0-flash')

def call_gemini(prompt):
    log_message("Passing prompt to LLM...")
    try:
        response = chat.send_message(
            message = prompt
        )
        text = remove_trailers(response.text) if "```" in response.text else response.text.strip()
        log_message(f"text zero: {text[0]}")
        if text[0].isalpha():
            text = get_content_between_curly_braces(text, "[", "]")

        log_message(f"Model Response: {text}\n")
        try:
            return literal_eval(text)
        except Exception as e:
            log_message(f"Model error: {e}", "error")
    except Exception as e:
        log_message(f"An error occurred: {e}", "error")
        return None
    
def remove_trailers(text):
    if '```' in text or 'json' in text:
        text = text.replace('```', "")
        text = text.replace('json', "")
        text = text.replace('python', "")
        return text.strip()
    return text
    