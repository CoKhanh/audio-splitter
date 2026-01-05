# Deployment Guide - Audio Splitter API on Google Cloud VM

This guide walks you through deploying the Audio Splitter FastAPI backend on a Google Cloud VM.

---

## Prerequisites

- Google Cloud account
- A VM instance with sufficient resources (minimum 8GB RAM for Demucs)
- SSH access to your VM

---

## Table of Contents

1. [VM Setup and Disk Configuration](#vm-setup-and-disk-configuration)
2. [Server Environment Setup](#server-environment-setup)
3. [Application Deployment](#application-deployment)
4. [Firewall Configuration](#firewall-configuration)
5. [Running the Application](#running-the-application)
6. [Accessing Your API](#accessing-your-api)
7. [Troubleshooting](#troubleshooting)

---

## VM Setup and Disk Configuration

### Step 1: Create Google Cloud VM

1. Go to [Google Cloud Console - Compute Engine](https://console.cloud.google.com/compute/instances)
2. Click **"CREATE INSTANCE"**
3. Configure:
   - **Name**: `audio-splitter-backend`
   - **Region**: Choose closest to your users
   - **Machine type**: `e2-standard-2` (2 vCPU, 8 GB RAM) minimum
   - **Boot disk**: Ubuntu 22.04 LTS, 50-100 GB
   - **Firewall**: Allow HTTP and HTTPS traffic
4. Click **"CREATE"**

### Step 2: Check Disk Space

SSH into your VM and check available space:

```bash
df -h
```

You should see at least 40GB available on `/dev/sda1`.

### Step 3: Increase Disk Size (If Needed)

If you need more space:

**In Google Cloud Console:**
1. Go to **Compute Engine > Disks**
2. Click on your VM's disk
3. Click **"EDIT"**
4. Increase **Size (GB)** to desired amount (50-100 GB recommended)
5. Click **"SAVE"**

**On your VM, expand the partition:**

```bash
# Install cloud utilities
sudo apt update
sudo apt install cloud-guest-utils -y

# Grow the partition
sudo growpart /dev/sda 1

# Resize the filesystem
sudo resize2fs /dev/sda1

# Verify new size
df -h
```

---

## Server Environment Setup

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Required System Packages

```bash
# Install FFmpeg (required by yt-dlp for audio conversion)
sudo apt install ffmpeg -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y
```

### Step 3: Upload Application Files

**From your local machine:**

```bash
# Navigate to your project
cd /Users/khanhcoduong/Documents/projects/audio-splitter/ezbeatv0

# Upload files to VM (replace YOUR_VM_IP with your actual IP)
scp -r * username@YOUR_VM_IP:~/audio-splitter/
```

**Or clone from Git (if using Git):**

```bash
# On the VM
cd ~
git clone YOUR_REPO_URL audio-splitter
cd audio-splitter
```

---

## Application Deployment

### Step 1: Create Python Virtual Environment

```bash
cd ~/audio-splitter

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 2: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This will install:
- FastAPI
- Uvicorn
- Demucs
- yt-dlp
- And other dependencies

**Note:** This may take 10-15 minutes as it downloads PyTorch and Demucs models.

### Step 3: Create Required Directories

```bash
mkdir -p separated/htdemucs downloads uploads
```

---

## Firewall Configuration

### Configure Google Cloud Firewall

You need to open the port your FastAPI app runs on (default: 8000).

**Method 1: Using Google Cloud Console**

1. Go to [VPC Network > Firewall](https://console.cloud.google.com/networking/firewalls/list)
2. Click **"CREATE FIREWALL RULE"**
3. Configure:
   - **Name**: `allow-port-8000`
   - **Direction of traffic**: Ingress
   - **Action on match**: Allow
   - **Targets**: All instances in the network
   - **Source IPv4 ranges**: `0.0.0.0/0`
   - **Protocols and ports**: TCP: `8000`
4. Click **"CREATE"**

**Method 2: Using gcloud Command**

```bash
gcloud compute firewall-rules create allow-port-8000 \
    --allow tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow FastAPI on port 8000"
```

---

## Running the Application

### Development Mode (with auto-reload)

```bash
cd ~/audio-splitter
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Important:** This runs in foreground - if you close terminal, the app stops!

### Production Mode (Recommended)

**Option 1: Using screen (keeps running after logout)**

```bash
# Install screen
sudo apt install screen -y

# Create a screen session
screen -S audio-splitter

# Activate venv and run
cd ~/audio-splitter
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Detach from screen: Press Ctrl+A, then D
# Reattach later: screen -r audio-splitter
```

**Option 2: Using systemd service (best for production)**

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/audio-splitter.service
```

Add this content:

```ini
[Unit]
Description=Audio Splitter FastAPI
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/audio-splitter
Environment="PATH=/home/YOUR_USERNAME/audio-splitter/venv/bin"
ExecStart=/home/YOUR_USERNAME/audio-splitter/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username.

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable audio-splitter

# Start the service
sudo systemctl start audio-splitter

# Check status
sudo systemctl status audio-splitter

# View logs
sudo journalctl -u audio-splitter -f
```

**Useful commands:**

```bash
# Stop the service
sudo systemctl stop audio-splitter

# Restart the service
sudo systemctl restart audio-splitter

# View logs
sudo journalctl -u audio-splitter -n 100
```

---

## Accessing Your API

### Get Your VM Public IP

```bash
curl ifconfig.me
```

Or check in Google Cloud Console under **Compute Engine > VM Instances** (External IP column).

### API Endpoints

Once running, your API will be available at:

- **Root**: `http://YOUR_PUBLIC_IP:8000/`
- **API Docs**: `http://YOUR_PUBLIC_IP:8000/docs`
- **Health Check**: `http://YOUR_PUBLIC_IP:8000/`

### Available Endpoints

1. **Upload and Separate**
   - **POST** `/separate`
   - Upload audio file and separate vocals/instrumentals

2. **Download from YouTube**
   - **POST** `/download-youtube`
   - Download audio from YouTube URL

3. **Download and Separate YouTube**
   - **POST** `/download-and-separate`
   - Download from YouTube and automatically separate
   - Supports email notifications

### Test Your API

```bash
# Test locally on VM
curl http://localhost:8000

# Test from your local machine
curl http://YOUR_PUBLIC_IP:8000
```

You should see: `{"Hello":"World"}`

---

## Troubleshooting

### Check if Service is Running

```bash
# Check process
ps aux | grep uvicorn

# Check port
sudo ss -tlnp | grep 8000

# Test locally
curl http://localhost:8000
```

### Check Logs

**If using screen:**
```bash
screen -r audio-splitter
```

**If using systemd:**
```bash
sudo journalctl -u audio-splitter -f
```

### Common Issues

#### 1. "Site can't be reached" from browser

**Solution:** Check firewall configuration
```bash
# Verify firewall rule exists
gcloud compute firewall-rules list | grep 8000

# Test from VM
curl http://localhost:8000
```

#### 2. "No space left on device"

**Solution:** Increase disk size (see [VM Setup](#vm-setup-and-disk-configuration))

#### 3. "Connection refused"

**Possible causes:**
- App not running: Check with `ps aux | grep uvicorn`
- Wrong host: Ensure you used `--host 0.0.0.0`, not just `--reload`
- Firewall blocking: Check firewall rules

#### 4. YouTube downloads failing with DNS error

**This happens on Hugging Face Spaces, NOT on Google Cloud VM**

If you see `[Errno -5] No address associated with hostname`, your VM likely has DNS issues. Google Cloud VMs should work fine with YouTube downloads.

#### 5. Out of memory errors

**Solution:** Upgrade to larger VM instance
- Demucs requires at least 8GB RAM
- Recommended: e2-standard-2 (8GB) or e2-standard-4 (16GB)

---

## Environment Variables (Optional)

For production, consider using environment variables for sensitive data:

```bash
# Create .env file
nano ~/audio-splitter/.env
```

Add:
```
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

Update your code to read from environment variables instead of hardcoding.

---

## Performance Optimization

### 1. Use Workers for Better Performance

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

**Note:** Don't use too many workers as Demucs is memory-intensive.

### 2. Monitor Resource Usage

```bash
# Check memory usage
free -h

# Check CPU usage
htop

# Check disk usage
df -h
```

### 3. Clean Up Old Files Periodically

Create a cron job to clean old separated files:

```bash
crontab -e
```

Add:
```
# Clean files older than 7 days every day at 2 AM
0 2 * * * find ~/audio-splitter/separated -type f -mtime +7 -delete
0 2 * * * find ~/audio-splitter/downloads -type f -mtime +7 -delete
```

---

## Security Recommendations

1. **Use HTTPS with a domain and SSL certificate** (use Nginx + Certbot)
2. **Implement rate limiting** to prevent abuse
3. **Use environment variables** for sensitive data
4. **Regularly update** system packages and Python dependencies
5. **Monitor logs** for suspicious activity
6. **Set up backups** of your application and data

---

## Cost Optimization

### Google Cloud Pricing (Approximate)

- **e2-standard-2** (8GB RAM): ~$49/month
- **Disk (50GB)**: ~$2/month
- **Total**: ~$51/month

### Alternative: Oracle Cloud Free Tier

If cost is a concern, consider **Oracle Cloud Free Tier**:
- **24 GB RAM, 4 vCPU ARM** - FREE FOREVER
- No network restrictions
- See Oracle Cloud setup guide for details

---

## Updating Your Application

To deploy updates:

```bash
# SSH into VM
cd ~/audio-splitter

# Pull latest changes (if using Git)
git pull

# Or upload new files from local machine
# scp -r * username@YOUR_VM_IP:~/audio-splitter/

# Activate venv
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart audio-splitter

# Or restart screen session
screen -r audio-splitter
# Ctrl+C to stop, then run uvicorn command again
```

---

## Next Steps

1. ✅ Set up domain name (optional but recommended)
2. ✅ Configure Nginx reverse proxy
3. ✅ Install SSL certificate with Certbot
4. ✅ Set up monitoring and alerts
5. ✅ Implement proper logging
6. ✅ Create automated backups

---

## Support

For issues or questions:
- Check logs: `sudo journalctl -u audio-splitter -f`
- Test locally: `curl http://localhost:8000`
- Verify firewall: Check Google Cloud firewall rules
- Check resources: `htop`, `free -h`, `df -h`

---

**Deployment Complete! 🎉**

Your Audio Splitter API should now be running and accessible at `http://YOUR_PUBLIC_IP:8000`
