from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def get_video_id(youtube_url: str) -> str:
    """
    Extract video ID from YouTube URL
    """
    parsed_url = urlparse(youtube_url)
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]
    elif parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    else:
        raise ValueError("Invalid YouTube URL")

def get_transcript(youtube_url: str, language: str = "en") -> str:
    """
    Fetch transcript for a given YouTube URL
    """
    video_id = get_video_id(youtube_url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
    
    # Join transcript into readable text
    return " ".join([entry["text"] for entry in transcript])

if __name__ == "__main__":
    url = input("Enter YouTube URL: ").strip()
    try:
        transcript_text = get_transcript(url)
        print("\nTranscript:\n")
        print(transcript_text)
    except Exception as e:
        print(f"Error: {e}")
