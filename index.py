import requests

# --- Configuration ---
# IMPORTANT: Directly scraping YouTube can be unreliable and may be blocked.
# For robust solutions, consider using the official YouTube Data API.
youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Example YouTube URL
output_filename = "youtube_page.html" # Name of the file to save the HTML to

# --- Fetch HTML Content and Save to File ---
print(f"Attempting to fetch HTML from: {youtube_url}")
try:
    response = requests.get(youtube_url)
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    html_content = response.text

    # Save the retrieved HTML to a file
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write(html_content)
    print(f"Successfully fetched HTML and saved it to '{output_filename}'")

except requests.exceptions.RequestException as e:
    print(f"Error fetching URL: {e}")
    print("HTML content could not be retrieved or saved.")
