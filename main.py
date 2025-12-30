from typing import Union
import asyncio
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import demucs.separate
import yt_dlp

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Create required directories if they don't exist
# Uncomment these lines if you want the server to auto-create directories on startup
# Path("separated/htdemucs").mkdir(parents=True, exist_ok=True)
# Path("downloads").mkdir(parents=True, exist_ok=True)

# Mount the separated folder as static files
app.mount("/audio", StaticFiles(directory="separated/htdemucs"), name="audio")

# Mount the downloads folder as static files
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/separate")
async def separate_audio(request: Request, file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Process the audio file
    await asyncio.to_thread(
        demucs.separate.main,
        ["--mp3", "--two-stems", "vocals", str(file_path)]
    )

    # Delete the uploaded file after processing
    if file_path.exists():
        file_path.unlink()

    # Get the output folder path (without extension)
    file_name_without_ext = Path(file.filename).stem
    output_folder = Path("separated/htdemucs") / file_name_without_ext

    # Build the base URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    # Collect all files in the output folder
    files_dict = {}
    if output_folder.exists():
        for file_path in output_folder.glob("*.mp3"):
            file_name_without_ext = file_path.stem
            # Create the public URL
            relative_path = file_path.relative_to("separated/htdemucs")
            file_url = f"{base_url}/audio/{relative_path}"
            files_dict[file_name_without_ext] = file_url

    return files_dict

@app.post("/download-youtube")
async def download_youtube_audio(request: Request):
    """Download audio from YouTube URL and return the file path"""
    body = await request.json()
    youtube_url = body.get("url")

    if not youtube_url:
        return {"error": "YouTube URL is required"}

    # Create downloads directory
    download_dir = Path("downloads")
    download_dir.mkdir(exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        # Download best available audio quality
        'format': 'bestaudio/best',

        # Post-processing: extract audio and convert to MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
            'preferredcodec': 'mp3',       # Convert to MP3 format
            'preferredquality': '192',     # Set bitrate to 192 kbps
        }],

        # Output template: save as "Video Title.mp3" in downloads directory
        'outtmpl': str(download_dir / '%(title)s.%(ext)s'),

        # Suppress console output
        'quiet': True,

        # Don't show warnings
        'no_warnings': True,

        # Set to False for playlist downloading
        'noplaylist': True,

        # Bypass SSL certificate verification (helps with some download issues)
        'nocheckcertificate': True,

        # Mimic a real browser to avoid 403 Forbidden errors
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

        # Use multiple player clients for better compatibility with YouTube
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']  # Try Android and web clients
            }
        }
    }

    try:
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, youtube_url, download=True)
            video_title = info['title']
            file_path = download_dir / f"{video_title}.mp3"

        # Build the public URL
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        file_url = f"{base_url}/downloads/{video_title}.mp3"

        return {
            "success": True,
            "file_path": str(file_path),
            "file_url": file_url,
            "title": video_title
        }
    except Exception as e:
        return {"error": str(e), "success": False}

@app.post("/download-and-separate")
async def download_and_separate_youtube_audio(request: Request):
    """Download audio from YouTube URL and automatically separate it"""
    body = await request.json()
    youtube_url = body.get("url")

    if not youtube_url:
        return {"error": "YouTube URL is required"}

    # Create downloads directory
    download_dir = Path("downloads")
    download_dir.mkdir(exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        # Download best available audio quality
        'format': 'bestaudio/best',

        # Post-processing: extract audio and convert to MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
            'preferredcodec': 'mp3',       # Convert to MP3 format
            'preferredquality': '192',     # Set bitrate to 192 kbps
        }],

        # Output template: save as "Video Title.mp3" in downloads directory
        'outtmpl': str(download_dir / '%(title)s.%(ext)s'),

        # Suppress console output
        'quiet': True,

        # Don't show warnings
        'no_warnings': True,

        # Download only single video, not playlist
        'noplaylist': True,

        # Bypass SSL certificate verification (helps with some download issues)
        'nocheckcertificate': True,

        # Mimic a real browser to avoid 403 Forbidden errors
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

        # Use multiple player clients for better compatibility with YouTube
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']  # Try Android and web clients
            }
        }
    }

    try:
        # Step 1: Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, youtube_url, download=True)
            video_title = info['title']
            downloaded_file_path = download_dir / f"{video_title}.mp3"

        # Step 2: Separate the audio
        await asyncio.to_thread(
            demucs.separate.main,
            ["--mp3", "--two-stems", "vocals", str(downloaded_file_path)]
        )

        # Step 3: Get the output folder path
        file_name_without_ext = Path(video_title).stem
        output_folder = Path("separated/htdemucs") / file_name_without_ext

        # Step 4: Build URLs for separated files
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        files_dict = {}

        if output_folder.exists():
            for file_path in output_folder.glob("*.mp3"):
                file_name = file_path.stem
                relative_path = file_path.relative_to("separated/htdemucs")
                file_url = f"{base_url}/audio/{relative_path}"
                files_dict[file_name] = file_url

        # Step 5: Delete the downloaded file after processing
        if downloaded_file_path.exists():
            downloaded_file_path.unlink()

        # Step 6: Return all information
        return {
            "success": True,
            "title": video_title,
            "separated_audio": files_dict
        }

    except Exception as e:
        return {"error": str(e), "success": False}