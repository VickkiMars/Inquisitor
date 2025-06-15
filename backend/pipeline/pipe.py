from backend.article_links import extract as art
from backend.chunking.base import chunk_text
from backend.documents import extract as doc
from backend.gemini_call.gemcall_v2 import call_gemini
from backend.generator.prompt_generator import map_type_to_prompt, generate_prompt, generate_question_type
from backend.log_helper.report import log_message
from backend.gemini_call.prime_parser import parse_gemini_question_blocks
from backend.gemini_call.parser import PythonListOutputParser
from langchain_core.output_parsers import StrOutputParser
from backend.youtube_link import extract as yt
from ast import literal_eval
from typing import List


def gem_pipe(chunks: List, num_questions) -> List:
    """
    Orchestrates the Gemini API calls for question generation.
    Returns a single generated question string.
    """
    output_length = round(num_questions/3)
    chunks = chunks[:output_length]

    inputs_ = [generate_question_type(c) for c in chunks]
    log_message("Question type prompts generated")
    log_message(f"Number of prompts: {len(inputs_)}")
    log_message(f"Number of questions: {num_questions}")
    
    results = call_gemini(inputs_, parser=PythonListOutputParser())
    log_message(f"Question types generated: type: {results[0]}")

    types = [map_type_to_prompt(z) for z in results]
    assert len(types)==len(results)

    questions = [generate_prompt(chunks[i], x) for i,x in enumerate(types)]

    response = call_gemini(questions, StrOutputParser())
    
    response = parse_gemini_question_blocks(response)
    log_message(f"Response length: {len(response)}")
    return response


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

    generated_questions = gem_pipe(chunks, num_questions)
    return generated_questions

def process_article(url: str, num_questions) -> List:
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
        return [],[] # Return empty list on article extraction failure
    if not article_content:
        return [], []
    chunks = []
    try:
        chunks = chunk_text(str(article_content))
    except Exception as e:
        log_message(f"Could not chunk article text: {e}", "error")
        return [] # Return empty list on chunking failure
    
    generated_questions = gem_pipe(chunks, num_questions)
    log_message(f"Generated Questions: {generated_questions}")
    return generated_questions, title

async def process_yt(url: str, num_questions:str) -> List[str]:
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
        return [], [] # Return empty list on transcription failure

    if not transcription:
        log_message(f"Transcription is empty: {transcription}")
        return "An error occurred",[]

    chunks = []
    try:
        chunks = chunk_text(transcription)
    except Exception as e:
        log_message(f"An error occurred while chunking the transcription: {e}", "error")
        return "An error occurred",[] # Return empty list on chunking failure
    
    generated_questions = await gem_pipe(chunks, num_questions)
    return generated_questions