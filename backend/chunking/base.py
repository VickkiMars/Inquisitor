from nltk.tokenize import sent_tokenize
from backend.log_helper.report import log_message
import nltk


nltk.download('punkt_tab')
# Function to remove references from the text
def remove_references(text):
    # Define the keyword for the references section (simple 'References')
    reference_keyword = "References"

    # Find the index of the 'References' section
    start_index = text.find(reference_keyword)
    if start_index != -1:
        # Cut the text before the references section
        return text[:start_index].strip()
    else:
        return text

def chunk_text(text: str, num_questions=5, chunk_size: int = 9) -> list[list[str]]:
    """
    Chunks the input text into groups of sentences.

    Args:
        text (str): The input text to be chunked.
        chunk_size (int): The number of sentences in each chunk. Defaults to 5.

    Returns:
        list[list[str]]: A list of lists, where each inner list is a chunk of sentences.
                         Returns an empty list if the input is not a string or if
                         the text is empty after reference removal.
    """
    log_message(text, 'error')
    if not isinstance(text, str):
        print("\n\n\nError: Text passed is not a string. Returning an empty list.\n\n\n")
        return []

    # Ensure chunk_size is a positive integer
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        print("\n\n\nWarning: chunk_size must be a positive integer. Using default chunk_size=5.\n\n\n")
        chunk_size = 5

    text = remove_references(text)

    # Handle cases where text might become empty after remove_references
    if not text.strip():
        return []

    sentences = sent_tokenize(text)
    x = round(num_questions / 3)
    chunks = []

    # Group sentences into chunks of the given size
    for i in range(0,  len(sentences), chunk_size):
        if len(chunks) >= x:
            return chunks
        else:
            chunks.append(sentences[i:i + chunk_size])
 
    log_message(f"Number of chunks: {len(chunks)}, Actual number of questions: {num_questions}, Possible nummber of questions: {len(chunks)*3}")

    return chunks

# Example Usage:
if __name__ == "__main__":
    sample_text = (
        "This is the first sentence. This is the second sentence. "
        "Here is the third sentence. And the fourth one. "
        "Finally, the fifth sentence. This is sentence six. "
        "Sentence seven follows. Sentence eight is here. [1] "
        "And the ninth sentence. The tenth one concludes. [2,3]"
    )

    print("--- Testing with default chunk_size (5) ---")
    chunks_default = chunk_text(sample_text)
    for i, chunk in enumerate(chunks_default):
        print(f"Chunk {i+1}: {chunk}")

    print("\n--- Testing with chunk_size = 3 ---")
    chunks_three = chunk_text(sample_text, chunk_size=3)
    for i, chunk in enumerate(chunks_three):
        print(f"Chunk {i+1}: {chunk}")

    print("\n--- Testing with non-string input ---")
    chunks_invalid_input = chunk_text(123)
    print(f"Result for invalid input: {chunks_invalid_input}")

    print("\n--- Testing with empty string after removal ---")
    chunks_empty_after_ref = chunk_text("[1][2][3]")
    print(f"Result for empty string after ref removal: {chunks_empty_after_ref}")

    print("\n--- Testing with large chunk_size (larger than text) ---")
    chunks_large = chunk_text(sample_text, chunk_size=100)
    for i, chunk in enumerate(chunks_large):
        print(f"Chunk {i+1}: {chunk}")