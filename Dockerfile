FROM python:3.10.9

# Install FFmpeg (required by yt-dlp for audio conversion)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY . .

# Create required directories for audio processing
RUN mkdir -p separated/htdemucs downloads uploads

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
