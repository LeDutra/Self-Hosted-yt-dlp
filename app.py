import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

# Directory inside the container where videos are stored
DOWNLOAD_DIR = '/downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    # Get all files sorted by newest first
    try:
        files = [f for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
    except Exception:
        files = []
    return render_template('index.html', files=files)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.form.get('url')
    convert_mp4 = request.form.get('convert') == 'on'
    
    if url:
        # Base yt-dlp command using standard paths
        cmd = ['yt-dlp', '-P', DOWNLOAD_DIR, url]
        
        # Automatically recode to web-friendly MP4/AAC via ffmpeg if checked
        if convert_mp4:
            cmd.extend(['--recode-video', 'mp4'])
            
        try:
            # Execute the download
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing yt-dlp: {e}")
            
    return redirect(url_for('index'))

@app.route('/videos/<filename>')
def serve_video(filename):
    # Allows viewing/downloading the file right from the browser interface
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)