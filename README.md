# Audio Splitter Backend

FastAPI application using Demucs for audio separation.

## Local Development

### Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the application
```bash
# Development mode
fastapi dev main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## VPS Deployment

### 1. Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and pip
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies (for audio processing)
sudo apt install ffmpeg libsndfile1 -y
```

### 2. Upload your project
```bash
# From your local machine
scp -r /path/to/be-2 user@your-vps-ip:/home/user/audio-splitter
```

### 3. Setup on VPS
```bash
# SSH into VPS
ssh user@your-vps-ip

# Navigate to project
cd /home/user/audio-splitter

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the application

#### Option A: Direct run (for testing)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Option B: Using systemd (recommended for production)
Create service file:
```bash
sudo nano /etc/systemd/system/audio-splitter.service
```

Add this content:
```ini
[Unit]
Description=Audio Splitter FastAPI Application
After=network.target

[Service]
User=your-username
Group=your-username
WorkingDirectory=/home/user/audio-splitter
Environment="PATH=/home/user/audio-splitter/venv/bin"
ExecStart=/home/user/audio-splitter/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable audio-splitter
sudo systemctl start audio-splitter
sudo systemctl status audio-splitter
```

### 5. Setup Nginx reverse proxy (optional but recommended)
```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/audio-splitter
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your VPS IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/audio-splitter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Verify deployment
```bash
# Check if app is running
curl http://localhost:8000

# Or from your browser
http://your-vps-ip:8000
```

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "Hello": "World"
}
```

### `POST /separate`
Upload an audio file and separate vocals from instrumentals using Demucs AI.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with `file` field containing the audio file

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/separate" \
  -F "file=@/path/to/your/song.mp3"
```

**Example using Python:**
```python
import requests

with open("song.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/separate",
        files={"file": f}
    )
print(response.json())
```

**Response:**
```json
{
  "vocals": "http://localhost:8000/audio/song/vocals.mp3",
  "no_vocals": "http://localhost:8000/audio/song/no_vocals.mp3"
}
```

### `GET /audio/{path}`
Static file serving for processed audio files. Access the URLs returned by `/separate` endpoint.

**Example:**
```
http://localhost:8000/audio/song/vocals.mp3
http://localhost:8000/audio/song/no_vocals.mp3
```

## How It Works

1. Upload an audio file via `POST /separate`
2. The file is saved temporarily to `uploads/` directory
3. Demucs AI processes the audio and separates vocals from instrumentals
4. Original uploaded file is automatically deleted
5. Separated tracks are saved in `separated/htdemucs/{filename}/`
6. Returns public URLs to download the separated tracks

## Directory Structure

```
be-2/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
├── uploads/            # Temporary upload directory (auto-cleaned)
└── separated/          # Output directory for processed audio
    └── htdemucs/       # Demucs model output
        └── {filename}/ # Per-file output folders
            ├── vocals.mp3
            └── no_vocals.mp3
```

## Notes

- The urllib3 warning on macOS (LibreSSL) won't appear on Linux VPS (uses OpenSSL)
- Make sure to configure firewall rules to allow port 80 (HTTP) or 443 (HTTPS)
- For production, consider using environment variables for sensitive configuration
- Uploaded files are automatically deleted after processing to save disk space
- Processed audio files are publicly accessible via the `/audio/` route
- The API uses the `mdx_extra` Demucs model with vocals/instrumentals separation
