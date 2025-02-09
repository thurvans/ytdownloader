from flask import Flask, request, render_template, jsonify, Response, send_file
import yt_dlp
import os
import json
import time

app = Flask(__name__)

# Folder penyimpanan sementara untuk video
OUTPUT_FOLDER = "downloads"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress_data = {}

def progress_hook(d):
    """Fungsi untuk menangani progress download"""
    global progress_data
    video_url = d.get("info_dict", {}).get("webpage_url", "")

    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        progress_data[video_url] = percent
    elif d['status'] == 'finished':
        progress_data[video_url] = "100%"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    global progress_data
    data = request.json
    clip_url = data.get('url')
    resolution = data.get('resolution', '1080')

    if not clip_url:
        return jsonify({"error": "Masukkan URL YouTube!"}), 400

    output_path = os.path.join(OUTPUT_FOLDER, "%(title)s.%(ext)s")

    ydl_opts = {
        'format': f'bestvideo[height={resolution}]+bestaudio/best',
        'outtmpl': output_path,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }

    progress_data[clip_url] = "0%"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clip_url, download=True)
        filename = ydl.prepare_filename(info)  # Dapatkan nama file yang dihasilkan

    return jsonify({"message": "Unduhan selesai!", "filename": filename})

@app.route('/get_file/<filename>')
def get_file(filename):
    """Mengirim file ke user setelah unduhan selesai"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

@app.route('/progress')
def get_progress():
    """Mengirim data progress ke frontend secara real-time"""
    def generate():
        while True:
            time.sleep(1)
            yield f"data: {json.dumps(progress_data)}\n\n"
    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
