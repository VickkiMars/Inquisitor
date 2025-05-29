from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from backend.log_helper.report import log_message

def transcribe(video_url, count=0):
    out = ""
    video_id = extract_video_id(video_url); log_message(f"Video ID: {video_id} EXtracted")
    try:
        trans = YouTubeTranscriptApi.get_transcript(video_id)
        for line in trans:
            out += f"{line['text']}\n"
        log_message("Transcript extracted")
        return out
    except Exception as e:
        if count == 3:
            log_message(f"An error occurred: {e}", "error")
        else:
            count += 1
            log_message(f"An error occured: Retrying {count}:\t{e}", "error")
            transcribe(video_id, count=count)

def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    
    if 'youtube.com' in url:
        query = urlparse(url).query
        params = parse_qs(query)
        return params.get('v', [None])[0]
    elif 'youtu.be' in url:
        return urlparse(url).path[1:]
    elif len(url) == 11:  # Direct video ID
        return url
    return None