FROM python:3.11-slim

# Install system dependencies and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install core dependencies
RUN pip install --no-cache-dir --upgrade pip flask yt-dlp

# Set working directory
WORKDIR /app

# Copy application files
COPY app.py /app/
COPY templates/ /app/templates/

# Create the internal volume point for saved data
RUN mkdir /downloads

# Expose the Flask web UI port
EXPOSE 5000

# Fire up the engine
CMD ["python", "app.py"]