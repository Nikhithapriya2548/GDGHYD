import os, time, threading, uuid, json, requests, logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from services.prompt_templates import detect_language, build_image_prompt, build_video_prompt, build_audio_prompt

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')

@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')
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
    required_vars = ['GEMINI_API_KEY']
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
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents="Reply with the word 'OK'."
        )
        if response.text:
            return jsonify({'gemini_api_key_valid': True, 'error': None})
    except Exception as e:
        return jsonify({'gemini_api_key_valid': False, 'error': str(e)})
    return jsonify({'gemini_api_key_valid': False, 'error': 'Unknown failure'})

campaign_store = {}

@app.route('/api/campaign/create', methods=['POST'])
def create_campaign():
    campaign_id = str(uuid.uuid4())
    req_data = request.get_json(silent=True) or {}
    product_name = req_data.get('product_name', 'Unknown Product')
    product_desc = req_data.get('product_desc', 'A great product.')
    
    try:
        from google import genai
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        
        prompt = f"""You are a Creative Director. Generate a campaign plan for this product:
Product Name: {product_name}
Description: {product_desc}

Provide the output in strict JSON.
Keys required: creative_direction, visual_style, recommended_theme, scene_descriptions (array of strings), music_mood.
Provide ONLY valid JSON, no markdown formatting."""
        
        response = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith('`json'): text = text[7:]
        if text.startswith('```json'): text = text[7:]
        if text.endswith('`'): text = text.rstrip('`')
        creative_plan = json.loads(text.strip())
    except Exception as e:
        logger.error(f"Real API call failed for Creative Director, falling back to stub: {e}")
        creative_plan = {
            'creative_direction': f'Campaign for {product_name}: {product_desc}',
            'visual_style': 'Cinematic',
            'recommended_theme': 'Modern',
            'scene_descriptions': [f'A beautiful shot of {product_name}'],
            'music_mood': 'Uplifting',
            '_stub_fallback': True,
            '_stub_reason': str(e)
        }
    
    campaign_store[campaign_id] = creative_plan
    return jsonify({'campaign_id': campaign_id, 'creative_plan': creative_plan})

@app.route('/api/campaign/<id>/theme', methods=['POST'])
def set_theme(id):
    req_data = request.get_json(silent=True, force=True) or {}
    theme = req_data.get('theme', 'Future Tech')
    if id in campaign_store:
        campaign_store[id]['theme'] = theme
    return jsonify({'status': 'success', 'theme': theme})

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
        from google import genai
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        
        # Get the creative plan scenes for THIS specific campaign
        plan = campaign_store.get(id, {})
        scenes_list = plan.get('scene_descriptions', [])
        base_prompt = scenes_list[0] if scenes_list else 'A cinematic scene.'
        
        prompt = build_image_prompt(base_prompt, detect_language(base_prompt))
        
        result = client.models.generate_content(
            model='gemini-3.1-flash-lite-image',
            contents=prompt
        )
        
        image_bytes = result.candidates[0].content.parts[0].inline_data.data
        filename = f'scene_{uuid.uuid4().hex[:8]}.png'
        output_file = os.path.join(UPLOAD_FOLDER, filename)
        with open(output_file, 'wb') as f:
            f.write(image_bytes)
            
        scenes = [{'scene_id': 's1', 'image_url': f'/static/uploads/{filename}', 'prompt': prompt, 'source': 'real'}]
    except Exception as e:
        logger.error(f"Real API call failed for Storyboard, falling back to stub: {e}")
        scenes = [
            {'scene_id': 's1', 'image_url': '/static/prebaked/scene1.jpg', 'prompt': 'stub', 'source': 'stub', '_stub_fallback': True, '_stub_reason': str(e)}
        ]
    return jsonify({'scenes': scenes})

def run_real_video_job(job_id, prompt, campaign_id):
    try:
        from google import genai
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        
        operation = client.models.generate_videos(
            model='veo-3.1-generate-preview',
            prompt=prompt
        )
        
        while not operation.done:
            time.sleep(5)
            operation = client.operations.get(operation=operation)
            
        if operation.error:
            raise Exception(f"Video generation failed: {operation.error}")
            
        videos = operation.result.generated_videos
        if not videos:
            raise Exception("No videos returned.")
            
        uri = videos[0].video.uri
        
        r = requests.get(uri, headers={'x-goog-api-key': os.environ.get('GEMINI_API_KEY')})
        if r.status_code != 200:
            raise Exception(f"Failed to download video: {r.status_code} {r.text}")
            
        filename = f'video_{uuid.uuid4().hex[:8]}.mp4'
        output_file = os.path.join(UPLOAD_FOLDER, filename)
        with open(output_file, 'wb') as f:
            f.write(r.content)
            
        video_url = f'/static/uploads/{filename}'
        video_jobs[job_id]['status'] = 'completed'
        video_jobs[job_id]['video_url'] = video_url
        if campaign_id in campaign_store:
            campaign_store[campaign_id]['video_url'] = video_url
    except Exception as e:
        logger.error(f"Real API call failed for Video, falling back to stub: {e}")
        time.sleep(5)
        video_url = '/static/prebaked/variation_cinematic.mp4'
        video_jobs[job_id]['status'] = 'completed'
        video_jobs[job_id]['video_url'] = video_url
        video_jobs[job_id]['_stub_fallback'] = True
        video_jobs[job_id]['_stub_reason'] = str(e)
        if campaign_id in campaign_store:
            campaign_store[campaign_id]['video_url'] = video_url

@app.route('/api/campaign/<id>/video/start', methods=['POST'])
def video_start(id):
    job_id = str(uuid.uuid4())
    video_jobs[job_id] = {'status': 'processing', 'video_url': None}
    
    req_data = request.get_json(silent=True, force=True) or {}
    base_prompt = req_data.get('prompt', 'A cool video scene')
    lang = detect_language(base_prompt)
    video_prompt = build_video_prompt(base_prompt, "cinematic pan", lang)
    
    threading.Thread(target=run_real_video_job, args=(job_id, video_prompt, id), daemon=True).start()
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
        req_data = request.get_json(silent=True, force=True) or {}
        mood = req_data.get('mood', 'energetic')
        audio_prompt = build_audio_prompt(mood, detect_language(mood))
        
        from google import genai
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        
        result = client.models.generate_content(
            model='lyria-3.5',
            contents=audio_prompt
        )
        
        audio_bytes = None
        for part in result.candidates[0].content.parts:
            if part.inline_data:
                audio_bytes = part.inline_data.data
                break
                
        if not audio_bytes:
            raise Exception("No audio blob returned by Lyria")
            
        filename = f'bgm_{uuid.uuid4().hex[:8]}.mp3'
        output_file = os.path.join(UPLOAD_FOLDER, filename)
        with open(output_file, 'wb') as f:
            f.write(audio_bytes)
            
        audio_url = f'/static/uploads/{filename}'
        if id in campaign_store:
            campaign_store[id]['audio_url'] = audio_url
            campaign_store[id]['mood'] = mood
            
        return jsonify({'audio_url': audio_url, 'mood': mood, 'status': 'success'})
    except Exception as e:
        logger.error(f"Real API call failed for Audio, falling back to stub: {e}")
        audio_url = '/static/prebaked/variation_cinematic.mp3'
        if id in campaign_store:
            campaign_store[id]['audio_url'] = audio_url
            campaign_store[id]['mood'] = 'Synthwave'
            
        return jsonify({
            'audio_url': audio_url, 
            'mood': 'Synthwave', 
            'status': 'success',
            '_stub_fallback': True,
            '_stub_reason': str(e)
        })

@app.route('/api/campaign/<id>/final', methods=['GET'])
def get_final(id):
    plan = campaign_store.get(id, {})
    return jsonify({
        'video_url': plan.get('video_url'), 
        'audio_url': plan.get('audio_url'), 
        'theme': plan.get('theme', 'N/A'),
        'mood': plan.get('mood', 'N/A'),
        'images': [], 
        'status': 'ready'
    })

if __name__ == '__main__':
    # Use 0.0.0.0 instead of localhost/127.0.0.1 for deployment
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)







