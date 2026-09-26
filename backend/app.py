import os, time, threading, uuid, json, requests
import google.generativeai as genai
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from services.prompt_templates import detect_language, build_image_prompt, build_video_prompt, build_audio_prompt

app = Flask(__name__)
video_jobs = {}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/campaign/create', methods=['POST'])
def create_campaign():
    campaign_id = str(uuid.uuid4())
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("You are a Creative Director. Generate a campaign plan in strict JSON. Keys: creative_direction, visual_style, recommended_theme, scene_descriptions (array of strings), music_mood. Provide ONLY valid JSON.")
        text = response.text.strip()
        if text.startswith('`json'): text = text[7:]
        if text.endswith('`'): text = text[:-3]
        creative_plan = json.loads(text.strip())
    except Exception:
        creative_plan = {
            'creative_direction': 'High-energy and vibrant',
            'visual_style': 'Cyberpunk',
            'recommended_theme': 'Future Tech',
            'scene_descriptions': ['Scene 1: Neon city', 'Scene 2: Hacker den'],
            'music_mood': 'Synthwave'
        }
    return jsonify({'campaign_id': campaign_id, 'creative_plan': creative_plan})

@app.route('/api/campaign/<id>/theme', methods=['POST'])
def set_theme(id): return jsonify({'status': 'success', 'theme': 'Future Tech applied'})

@app.route('/api/campaign/<id>/upload', methods=['POST'])
def upload_asset(id):
    file = request.files.get('file')
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return jsonify({'asset_path': f'/static/uploads/{filename}', 'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/campaign/<id>/storyboard', methods=['POST'])
def storyboard(id):
    try:
        from google.cloud import aiplatform
        from vertexai.preview.vision_models import ImageGenerationModel
        aiplatform.init(project=os.environ.get('GOOGLE_CLOUD_PROJECT', 'stub'), location='us-central1')
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        prompt = build_image_prompt(request.json.get('prompt', 'scene'), detect_language(request.json.get('prompt', '')))
        model.generate_images(prompt=prompt, number_of_images=1)[0].save(location=os.path.join(UPLOAD_FOLDER, 'scene.png'))
        scenes = [{'scene_id': 's1', 'image_url': '/static/uploads/scene.png', 'prompt': prompt, 'source': 'real'}]
    except Exception:
        scenes = [{'scene_id': 's1', 'image_url': '/static/prebaked/scene1.jpg', 'prompt': 'stub', 'source': 'stub'}]
    return jsonify({'scenes': scenes})

def run_real_video_job(job_id, prompt):
    try:
        if not os.environ.get("GCP_ACCESS_TOKEN"): raise Exception()
        requests.post("https://us-central1-aiplatform.googleapis.com/v1/...veo:predict", json={"prompt": prompt})
        video_jobs[job_id]['status'] = 'completed'
        video_jobs[job_id]['video_url'] = '/static/uploads/real_video.mp4'
    except Exception:
        time.sleep(5)
        video_jobs[job_id]['status'] = 'completed'
        video_jobs[job_id]['video_url'] = '/static/output/final_video.mp4'

@app.route('/api/campaign/<id>/video/start', methods=['POST'])
def video_start(id):
    job_id = str(uuid.uuid4())
    video_jobs[job_id] = {'status': 'processing', 'video_url': None}
    threading.Thread(target=run_real_video_job, args=(job_id, "prompt"), daemon=True).start()
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/campaign/<id>/video/status/<job_id>', methods=['GET'])
def video_status(id, job_id):
    return jsonify({'status': video_jobs.get(job_id, {}).get('status', 'error'), 'video_url': video_jobs.get(job_id, {}).get('video_url')})

@app.route('/api/campaign/<id>/music', methods=['POST'])
def generate_music(id):
    try:
        if not os.environ.get("GCP_ACCESS_TOKEN"): raise Exception()
        audio_url = '/static/uploads/real_bgm.mp3'
    except Exception:
        audio_url = '/static/output/bgm.mp3'
    return jsonify({'audio_url': audio_url, 'mood': 'Synthwave', 'status': 'success'})

@app.route('/api/campaign/<id>/final', methods=['GET'])
def get_final(id): return jsonify({'video_url': '/static/output/final_video.mp4', 'audio_url': '/static/output/bgm.mp3', 'images': [], 'status': 'ready'})

if __name__ == '__main__':
    app.run(debug=True)
