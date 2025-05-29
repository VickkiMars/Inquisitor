import trafilatura
from urllib.parse import urlparse
# Add this after extraction:
import re
from backend.log_helper.report import log_message

def is_valid_url(url):
    """Check if the URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def sanitize_filename(title):
    """Clean the title to create a valid filename"""
    return re.sub(r'[\\/*?:"<>|]', '', title.strip())

def extract_and_save_text(url):
    """Extract text from URL and save to a file"""
    if not is_valid_url(url):
        log_message("Invalid URL format. Please include http:// or https://", "error")
        return

    try:
        # Download and extract text
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        #language = detect_language(text)

        if not text:
            log_message("No extractable text found on this page","error")
            return

        # Get page title for filename
        try:
            title = trafilatura.extract_metadata(downloaded).title
        except Exception as e:
            log_message(f"Couldn't retrieve article title: {e}", "error")
        return text, title
    
    except Exception as e:
        log_message(f"Error while extracting link: {e}", "error")

if __name__ == "__main__":
    print("Web Text Extractor (using Trafilatura)")
    url = input("Enter URL: ").strip()
    extract_and_save_text(url)