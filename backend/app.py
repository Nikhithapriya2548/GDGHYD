from flask import Flask, request, jsonify, send_from_directory
import time
import uuid

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')

@app.route('/')
def index():
    return send_from_directory('../frontend/templates', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend/static', path)

@app.route('/api/campaign/create', methods=['POST'])
def create_campaign():
    return jsonify({
        "campaign_id": str(uuid.uuid4()),
        "creative_plan": {
            "creative_direction": "High energy product showcase",
            "visual_style": "Modern, sleek",
            "recommended_theme": "Cinematic",
            "scene_descriptions": ["Intro shot of product", "Features highlight", "Outro with logo"],
            "music_mood": "Upbeat electronic"
        }
    })

@app.route('/api/campaign/<id>/theme', methods=['POST'])
def set_theme(id):
    data = request.json
    return jsonify({
        "status": "success",
        "theme": data.get("theme", "cinematic")
    })

@app.route('/api/campaign/<id>/upload', methods=['POST'])
def upload_asset(id):
    return jsonify({
        "asset_path": f"/static/uploads/{uuid.uuid4()}.png",
        "status": "success"
    })

@app.route('/api/campaign/<id>/storyboard', methods=['POST'])
def generate_storyboard(id):
    return jsonify({
        "scenes": [
            {"scene_id": 1, "image_url": "https://via.placeholder.com/150", "prompt": "Intro shot", "source": "ai"},
            {"scene_id": 2, "image_url": "https://via.placeholder.com/150", "prompt": "Feature highlight", "source": "ai"}
        ]
    })

@app.route('/api/campaign/<id>/video/start', methods=['POST'])
def start_video(id):
    return jsonify({
        "job_id": str(uuid.uuid4()),
        "status": "started"
    })

jobs = {}
@app.route('/api/campaign/<id>/video/status/<job_id>', methods=['GET'])
def video_status(id, job_id):
    if job_id not in jobs:
        jobs[job_id] = 0
    jobs[job_id] += 1
    
    if jobs[job_id] < 3:
        return jsonify({"status": "processing", "video_url": None})
    return jsonify({"status": "completed", "video_url": "https://www.w3schools.com/html/mov_bbb.mp4"})

@app.route('/api/campaign/<id>/music', methods=['POST'])
def generate_music(id):
    return jsonify({
        "audio_url": "https://www.w3schools.com/html/horse.ogg",
        "mood": "Upbeat",
        "status": "success"
    })

@app.route('/api/campaign/<id>/final', methods=['GET'])
def get_final(id):
    return jsonify({
        "video_url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "audio_url": "https://www.w3schools.com/html/horse.ogg",
        "images": ["https://via.placeholder.com/150"],
        "theme": "cinematic",
        "mood": "Upbeat",
        "status": "completed"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
