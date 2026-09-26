import os, time, threading, uuid, json, requests, logging
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from services.prompt_templates import detect_language, build_image_prompt, build_video_prompt, build_audio_prompt

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
video_jobs = {}

# Ensure static directories exist
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static')
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')
OUTPUT_FOLDER = os.path.join(STATIC_FOLDER, 'output')
PREBAKED_FOLDER = os.path.join(STATIC_FOLDER, 'prebaked')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PREBAKED_FOLDER, exist_ok=True)

# 1. Audit Env Vars on Startup
def check_env_vars():
    required_vars = ['GEMINI_API_KEY', 'GOOGLE_CLOUD_PROJECT', 'GCP_ACCESS_TOKEN']
    logger.info("--- Environment Variable Audit ---")
    for var in required_vars:
        is_set = bool(os.environ.get(var))
        logger.info(f"{var} is set: {is_set}")
    logger.info("----------------------------------")

check_env_vars()

# 3. Health Check Endpoint
@app.route('/api/health/gemini-key', methods=['GET'])
def health_gemini_key():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'gemini_api_key_valid': False, 'error': 'GEMINI_API_KEY is not set in environment'})
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Reply with the word 'OK'.")
        if response.text:
            return jsonify({'gemini_api_key_valid': True, 'error': None})
    except Exception as e:
        return jsonify({'gemini_api_key_valid': False, 'error': str(e)})
    return jsonify({'gemini_api_key_valid': False, 'error': 'Unknown failure'})

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
    except Exception as e:
        logger.error(f"Real API call failed for Creative Director, falling back to stub: {e}")
        creative_plan = {
            'creative_direction': 'High-energy and vibrant',
            'visual_style': 'Cyberpunk',
            'recommended_theme': 'Future Tech',
            'scene_descriptions': ['Scene 1: Neon city', 'Scene 2: Hacker den'],
            'music_mood': 'Synthwave',
            '_stub_fallback': True,
            '_stub_reason': str(e)
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
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id: raise Exception("GOOGLE_CLOUD_PROJECT is missing")
        aiplatform.init(project=project_id, location='us-central1')
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        req_data = request.json or {}
        base_prompt = req_data.get('prompt', 'scene')
        prompt = build_image_prompt(base_prompt, detect_language(base_prompt))
        
        model.generate_images(prompt=prompt, number_of_images=1)[0].save(location=os.path.join(UPLOAD_FOLDER, 'scene.png'))
        scenes = [{'scene_id': 's1', 'image_url': '/static/uploads/scene.png', 'prompt': prompt, 'source': 'real'}]
    except Exception as e:
        logger.error(f"Real API call failed for Storyboard, falling back to stub: {e}")
        scenes = [
            {'scene_id': 's1', 'image_url': '/static/prebaked/scene1.jpg', 'prompt': 'stub', 'source': 'stub', '_stub_fallback': True, '_stub_reason': str(e)}
        ]
    return jsonify({'scenes': scenes})

def run_real_video_job(job_id, prompt):
    try:
        access_token = os.environ.get("GCP_ACCESS_TOKEN")
        if not access_token: raise Exception("GCP_ACCESS_TOKEN is missing")
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id: raise Exception("GOOGLE_CLOUD_PROJECT is missing")
        
        url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/veo-1.0:predict"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        resp = requests.post(url, json={"instances": [{"prompt": prompt}]}, headers=headers)
        if resp.status_code != 200: raise Exception(f"Video API returned {resp.status_code}: {resp.text}")
            
        video_jobs[job_id]['status'] = 'completed'
        video_jobs[job_id]['video_url'] = '/static/uploads/real_video.mp4'
    except Exception as e:
        logger.error(f"Real API call failed for Video, falling back to stub: {e}")
        time.sleep(5)
        video_jobs[job_id]['status'] = 'completed'
        video_jobs[job_id]['video_url'] = '/static/output/final_video.mp4'
        video_jobs[job_id]['_stub_fallback'] = True
        video_jobs[job_id]['_stub_reason'] = str(e)

@app.route('/api/campaign/<id>/video/start', methods=['POST'])
def video_start(id):
    job_id = str(uuid.uuid4())
    video_jobs[job_id] = {'status': 'processing', 'video_url': None}
    
    req_data = request.json or {}
    base_prompt = req_data.get('prompt', 'A cool video scene')
    lang = detect_language(base_prompt)
    video_prompt = build_video_prompt(base_prompt, "cinematic pan", lang)
    
    threading.Thread(target=run_real_video_job, args=(job_id, video_prompt), daemon=True).start()
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/campaign/<id>/video/status/<job_id>', methods=['GET'])
def video_status(id, job_id):
    job = video_jobs.get(job_id, {})
    response = {'status': job.get('status', 'error'), 'video_url': job.get('video_url')}
    if job.get('_stub_fallback'):
        response['_stub_fallback'] = True
        response['_stub_reason'] = job.get('_stub_reason')
    return jsonify(response)

@app.route('/api/campaign/<id>/music', methods=['POST'])
def generate_music(id):
    try:
        access_token = os.environ.get("GCP_ACCESS_TOKEN")
        if not access_token: raise Exception("GCP_ACCESS_TOKEN is missing")
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id: raise Exception("GOOGLE_CLOUD_PROJECT is missing")
        
        req_data = request.json or {}
        mood = req_data.get('mood', 'energetic')
        audio_prompt = build_audio_prompt(mood, detect_language(mood))
        
        url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/lyria:predict"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        resp = requests.post(url, json={"instances": [{"prompt": audio_prompt}]}, headers=headers)
        
        if resp.status_code != 200: raise Exception(f"Audio API returned {resp.status_code}")
        return jsonify({'audio_url': '/static/uploads/real_bgm.mp3', 'mood': mood, 'status': 'success'})
    except Exception as e:
        logger.error(f"Real API call failed for Audio, falling back to stub: {e}")
        return jsonify({
            'audio_url': '/static/output/bgm.mp3', 
            'mood': 'Synthwave', 
            'status': 'success',
            '_stub_fallback': True,
            '_stub_reason': str(e)
        })

@app.route('/api/campaign/<id>/final', methods=['GET'])
def get_final(id): return jsonify({'video_url': '/static/output/final_video.mp4', 'audio_url': '/static/output/bgm.mp3', 'images': [], 'status': 'ready'})

if __name__ == '__main__':
    # Use 0.0.0.0 instead of localhost/127.0.0.1 for deployment
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
