from backend.article_links import extract as art
from backend.chunking.base import chunk_text
from backend.documents import extract as doc
from backend.gemini_call.gemcall import call_gemini
from backend.generator.prompt_generator import map_type_to_prompt, generate_prompt, generate_question_type
from backend.log_helper.report import log_message
from backend.pipeline.helper import get_content_between_curly_braces
from backend.youtube_link import extract as yt
from ast import literal_eval
from typing import List

def gem_pipe(chunk: str) -> str:
    """
    Orchestrates the Gemini API calls for question generation.
    Returns a single generated question string.
    """
    question_type = None
    try:
        # LLMs exist, so this call should ideally return a string representation of a list/tuple
        # that can be safely evaluated by literal_eval.
        question_type_raw = call_gemini(generate_question_type(chunk))
        log_message(f"Question type: {question_type_raw}")
        question_type = question_type_raw
    except (ValueError, SyntaxError) as e:
        log_message(f"Error evaluating question type from Gemini: {e}. Raw response: {question_type_raw}", "error")
        # Handle cases where literal_eval fails, e.g., default to a common type or raise specific error
    except Exception as e:
        log_message(f"An error occurred while generating question type: {e}","error")


    ttp = None
    try:
        if question_type: # Only proceed if question_type was successfully determined
            ttp = call_gemini(map_type_to_prompt(question_type))
    except Exception as e:
        log_message(f"An error occurred while mapping question type: {e}","error")

    questions = "" # Initialize questions as an empty string
    try:
        if ttp: # Only proceed if ttp was successfully determined
            questions = call_gemini(generate_prompt(chunk, ttp))
    except Exception as e:
        log_message(f"An error occurred while generating questions: {e}","error")

    return questions


## Modified Processing Functions
def process_document(file_path: str, num_questions: int) -> List[str]:
    """
    Processes a document from a file path, chunks its content,
    and generates a specified number of questions.
    Returns a list of generated questions.
    """
    document_content = None
    try:
        content_extractor = doc.Document(file_path=file_path, num_questions=num_questions)
        document_content = content_extractor.text
        # num is already available from input num_questions, using it consistently
    except Exception as e:
        log_message(f"Could not process document: {e}", "error")
        return [] # Return empty list on document processing failure

    if not document_content:
        return [] # Ensure we don't proceed if content extraction failed

    chunks = []
    try:
        chunks = chunk_text(document_content)
    except Exception as e:
        log_message(f"Could not chunk text: {e}", "error")
        return [] # Return empty list on chunking failure

    generated_questions = []
    count = 0
    for chunk in chunks:
        if count >= num_questions: # Changed from == to >= to ensure num_questions is respected even if a chunk yields multiple questions or if we only need a few.
            break

        try:
            # Assuming gem_pipe returns a single question string or a string that contains multiple questions separated
            # We'll split it if it returns multiple questions in one go.
            question_output = gem_pipe(chunk)
            # Assuming gem_pipe might return a string with multiple questions (e.g., "1. Q1\n2. Q2").
            # You might need more sophisticated parsing here depending on gem_pipe's exact output format.
            # For simplicity, we'll assume it returns a single question string for now or a string that can be treated as one question.
            generated_questions.append(question_output)
            count += 1 # Increment for each question appended. If gem_pipe returns multiple questions in one call, you'd increment by the number of questions returned.
        except Exception as e:
            log_message(f"An error occurred during question generation for a chunk: {e}", "error")
            # Decide whether to continue or break on error; here, we continue to try other chunks.

    return generated_questions

def process_article(url: str, num_questions: int = 10) -> List[str]:
    """
    Processes an article from a URL, chunks its content,
    and generates questions.
    Returns a list of generated questions.
    """
    article_content = None
    try:
        article_content, title = art.extract_and_save_text(url)
    except Exception as e:
        log_message(f"Could not extract article text from URL {url}: {e}", "error")
        return [] # Return empty list on article extraction failure

    if not article_content:
        return []

    chunks = []
    try:
        chunks = chunk_text(str(article_content))
    except Exception as e:
        log_message(f"Could not chunk article text: {e}", "error")
        return [] # Return empty list on chunking failure

    generated_questions = []
    count = 0
    for chunk in chunks:
        if count >= num_questions:
            break
        try:
            question_output = gem_pipe(chunk)
            for i in question_output:
                generated_questions.append(i)
            count += 1
        except Exception as e:
            log_message(f"An error occurred during question generation for an article chunk: {e}", "error")
    return generated_questions, title

def process_yt(url: str) -> List[str]:
    """
    Processes a YouTube video by transcribing it, chunking the transcription,
    and generating questions.
    Returns a list of generated questions.
    """
    transcription = None
    try:
        transcription = yt.transcribe(video_url=url)
    except Exception as e:
        log_message(f"An error occurred during YouTube transcription for URL {url}: {e}", "error")
        return [] # Return empty list on transcription failure

    if not transcription:
        return []

    chunks = []
    try:
        chunks = chunk_text(transcription)
    except Exception as e:
        log_message(f"An error occurred while chunking the transcription: {e}", "error")
        return [] # Return empty list on chunking failure

    generated_questions = []
    for chunk in chunks:
        try:
            response = gem_pipe(chunk)
            log_message(f"Gemini response: {response[:50]}...") # Log a snippet for brevity
            generated_questions.append(response)
        except Exception as e:
            log_message(f"An error occurred while getting Gemini's response for a YouTube chunk: {e}", "error")
    return generated_questions