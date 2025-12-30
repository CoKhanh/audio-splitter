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

- `GET /` - Health check
- `GET /items/{item_id}` - Example endpoint with query parameter

## Notes

- The urllib3 warning on macOS (LibreSSL) won't appear on Linux VPS (uses OpenSSL)
- Make sure to configure firewall rules to allow port 80 (HTTP) or 443 (HTTPS)
- For production, consider using environment variables for sensitive configuration
