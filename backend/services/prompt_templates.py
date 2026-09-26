import re

def detect_language(text):
    if re.search(r'[\u0C00-\u0C7F]', text):
        return 'telugu'
    return 'english'

def build_image_prompt(base_prompt, language='english'):
    if language == 'telugu':
        return f"Generate a culturally relevant and vibrant image for a Telugu audience based on: '{base_prompt}'. Cinematic lighting, high quality."
    return f"Generate a high-quality, visually appealing image based on: '{base_prompt}'. Cinematic lighting, 4k."

def build_video_prompt(image_description, motion_instruction, language='english'):
    if language == 'telugu':
        return f"Create a dynamic video scene from this image: '{image_description}'. The motion should be: {motion_instruction}. Incorporate vibrant, energetic elements suitable for a festive Telugu theme."
    return f"Create a dynamic video scene from this image: '{image_description}'. The motion should be: {motion_instruction}. Smooth, professional camera movement."

def build_audio_prompt(mood, language='english'):
    if language == 'telugu':
        return f"Create a background music track with a {mood} mood. Incorporate traditional Telugu or South Indian instruments like the flute, mridangam, or veena, blending with modern beats."
    return f"Create a background music track with a {mood} mood. High quality, professional production, instrumental only."
