from typing import Union
import asyncio
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import unicodedata

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

    try:
        # Generate hash from URL for filename
        title_hash = str(abs(hash(youtube_url)))[:12]

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

            # Output template: use hash-based filename
            'outtmpl': str(download_dir / f'{title_hash}.%(ext)s'),

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

        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, youtube_url, download=True)
            video_title = info['title']
            file_path = download_dir / f"{title_hash}.mp3"

        # Build the public URL
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        file_url = f"{base_url}/downloads/{title_hash}.mp3"

        return {
            "success": True,
            "file_path": str(file_path),
            "file_url": file_url,
            "title": video_title,
            "hash": title_hash
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def send_email_notification(to_email: str, video_title: str, files_dict: dict, base_url: str):
    """Send email with separated audio download links"""
    # Email configuration (you should move these to environment variables)
    sender_email = "duongcokhanh17110315@gmail.com"  # Replace with your email
    sender_password = "evet bbrd cwgp mbxz"  # Replace with your app password

    # Create email message
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = f"Audio Separation Complete: {video_title}"

    # Create HTML email body with colorful design
    html_body = f"""
    <html>
      <head>
        <meta charset="UTF-8">
      </head>
      <body style="margin: 0; padding: 2px; background: linear-gradient(135deg, #e0e7ff 0%, #f3e7e9 100%); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <div style="max-width: 600px; margin: 40px auto; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">

          <!-- Header with gradient -->
          <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
            <div style="font-size: 60px; margin-bottom: 10px;">🎵✨</div>
            <h1 style="color: white; margin: 0; font-size: 28px; font-weight: bold;">Your Audio is Ready!</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Separation complete 🎉</p>
          </div>

          <!-- Content -->
          <div style="padding: 40px 30px; background: white">

            <!-- Video info card -->
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 15px; padding: 20px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);">
              <p style="color: white; margin: 0; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">🎬 Video Title</p>
              <p style="color: white; margin: 0; font-size: 18px; font-weight: bold; line-height: 1.4;">{video_title}</p>
            </div>

            <!-- Download section -->
            <div style="margin-bottom: 30px;">
              <h2 style="color: #333; font-size: 22px; margin: 0 0 20px 0; display: flex; align-items: center;">
                <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                  🎧 Your Separated Tracks
                </span>
              </h2>

              <div style="space-y: 15px;">
    """

    # Add download buttons for each file
    colors = [
        ("linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "🎤"),  # Purple gradient for vocals
        ("linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "🎸"),  # Pink gradient for instrumentals
    ]

    for idx, (file_name, file_url) in enumerate(files_dict.items()):
        gradient, emoji = colors[idx % len(colors)]
        html_body += f"""
                <a href="{file_url}" style="display: block; text-decoration: none; background: {gradient}; color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: transform 0.2s;">
                  <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                      <span style="font-size: 28px; margin-right: 15px;">{emoji}</span>
                      <div>
                        <p style="margin: 0; font-size: 16px; font-weight: bold; text-transform: capitalize;">{file_name.replace('_', ' ')}</p>
                        <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">Click to download</p>
                      </div>
                    </div>
                    <span style="font-size: 24px;">⬇️</span>
                  </div>
                </a>
        """

    html_body += """
              </div>
            </div>

            <!-- Info box -->
            <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); border-radius: 12px; padding: 20px; margin-bottom: 30px;">
              <p style="margin: 0; color: #8B4513; font-size: 14px; line-height: 1.6;">
                <strong>💡 Tip:</strong> These files will remain available while the server is running. Download them now to keep them forever!
              </p>
            </div>

            <!-- Footer -->
            <div style="text-align: center; padding-top: 20px; border-top: 2px solid #f0f0f0;">
              <p style="color: #666; font-size: 14px; margin: 0 0 10px 0;">Made with 💜 by</p>
              <p style="color: #667eea; font-size: 18px; font-weight: bold; margin: 0;">Khanh DC</p>
              <p style="color: #999; font-size: 12px; margin: 15px 0 0 0;">Powered by EZBeat</p>
            </div>

          </div>

        </div>

      </body>
    </html>
    """

    # Attach HTML body
    msg.attach(MIMEText(html_body, 'html'))

    # Send email using Gmail SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.post("/download-and-separate")
async def download_and_separate_youtube_audio(request: Request):
    """Download audio from YouTube URL and automatically separate it"""
    body = await request.json()
    youtube_url = body.get("url")
    email = body.get("email")  # Optional email parameter

    if not youtube_url:
        return {"error": "YouTube URL is required"}

    # Create downloads directory
    download_dir = Path("downloads")
    download_dir.mkdir(exist_ok=True)

    try:
        # Step 1: Generate hash from URL for filename
        title_hash = str(abs(hash(youtube_url)))[:12]

        # Step 2: Configure yt-dlp options with hash-based filename
        ydl_opts = {
            # Download best available audio quality
            'format': 'bestaudio/best',

            # Post-processing: extract audio and convert to MP3
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
                'preferredcodec': 'mp3',       # Convert to MP3 format
                'preferredquality': '192',     # Set bitrate to 192 kbps
            }],

            # Output template: use hash-based filename
            'outtmpl': str(download_dir / f'{title_hash}.%(ext)s'),

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

        # Download the audio and get video title
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, youtube_url, download=True)
            video_title = info['title']
            file_path = download_dir / f"{title_hash}.mp3"

        # Step 3: Separate the audio using hash-based filename
        await asyncio.to_thread(
            demucs.separate.main,
            ["--mp3", "--two-stems", "vocals", str(file_path)]
        )

        # Step 4: Get the output folder path using hash-based filename
        output_folder = Path("separated/htdemucs") / title_hash

        # Step 4: Build URLs for separated files
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        files_dict = {}

        if output_folder.exists():
            for separated_file in output_folder.glob("*.mp3"):
                file_name = separated_file.stem
                relative_path = separated_file.relative_to("separated/htdemucs")
                file_url = f"{base_url}/audio/{relative_path}"
                files_dict[file_name] = file_url

        # Step 5: Send email notification if email is provided
        email_sent = False
        if email:
            email_sent = await asyncio.to_thread(
                send_email_notification,
                email,
                video_title,
                files_dict,
                base_url
            )

        # Step 6: Delete the downloaded file after processing (NOT the separated files)
        if file_path.exists():
            file_path.unlink()

        # Step 7: Return all information
        return {
            "success": True,
            "title": video_title,
            "separated_audio": files_dict,
            "email_sent": email_sent
        }

    except Exception as e:
        return {"error": str(e), "success": False}