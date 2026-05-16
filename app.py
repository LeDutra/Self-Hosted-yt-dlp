import os
import subprocess
import tempfile
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

# Directory inside the container where videos are stored
DOWNLOAD_DIR = '/library/Videos'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    # Get all files sorted by newest first
    files_data = []
    try:
        files = [f for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
        for f in files:
            size_bytes = os.path.getsize(os.path.join(DOWNLOAD_DIR, f))
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
            files_data.append({'name': f, 'size': size_str})
    except Exception:
        pass
    error = request.args.get('error')
    success = request.args.get('success')
    return render_template('index.html', files=files_data, error=error, success=success)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.form.get('url')
    convert_mp4 = request.form.get('convert') == 'on'
    cookies_file = request.files.get('cookies_file')
    
    if url:
        # Base yt-dlp command using standard paths
        cmd = ['yt-dlp', '-P', DOWNLOAD_DIR, url]
        
        # Automatically recode to web-friendly MP4/AAC via ffmpeg if checked
        if convert_mp4:
            cmd.extend(['--recode-video', 'mp4'])
            
        temp_cookie_path = None
        if cookies_file and cookies_file.filename:
            # Create a secure temporary file to store the uploaded cookies
            fd, temp_cookie_path = tempfile.mkstemp(suffix='.txt')
            os.close(fd) # Close descriptor, let Flask save handle the writing
            cookies_file.save(temp_cookie_path)
            cmd.extend(['--cookies', temp_cookie_path])
            
        try:
            # Execute the download
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing yt-dlp: {e.stderr}")
            error_msg = e.stderr.lower() if e.stderr else ""
            if any(k in error_msg for k in ['sign in', 'login', 'cookie', 'members', 'private', 'authentication']):
                return redirect(url_for('index', error='auth'))
            return redirect(url_for('index', error='failed'))
        finally:
            # Clean up the temporary cookie file regardless of success or failure
            if temp_cookie_path and os.path.exists(temp_cookie_path):
                os.remove(temp_cookie_path)
            
        return redirect(url_for('index', success=1))
            
    return redirect(url_for('index'))

@app.route('/play/<path:filename>')
def play_video(filename):
    # Serve the video file inline for browser playback
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=False)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/delete/<path:filename>', methods=['POST'])
def delete_video(filename):
    # Prevent directory traversal and remove the selected file
    file_path = os.path.normpath(os.path.join(DOWNLOAD_DIR, filename))
    if os.path.commonpath([DOWNLOAD_DIR, file_path]) == DOWNLOAD_DIR and os.path.isfile(file_path):
        os.remove(file_path)
    return redirect(url_for('index'))

@app.route('/library/Videos/<filename>')
def serve_video(filename):
    # Allows viewing/downloading the file right from the browser interface
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)