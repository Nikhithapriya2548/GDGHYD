# CampaignFlow 🚀

**CampaignFlow** is an end-to-end AI agent and marketing pipeline that acts as your personal creative agency. It compresses the traditional, weeks-long marketing production process into just a few minutes. 

Simply input a product idea (in English or regional languages like Telugu!), and CampaignFlow automatically writes a creative plan, generates 4K storyboard images, renders cinematic AI videos, and composes custom background music perfectly tailored to your campaign.

---

## ✨ Features

- **🧠 AI Creative Planner**: Leverages Gemini (e.g., `gemini-3.1-pro-preview`) to digest your product description and output a multi-scene marketing storyboard and concept.
- **🎨 Visual Storyboarding**: Uses `gemini-3.1-flash-lite-image` to generate 4K, highly detailed storyboard visuals that match your selected theme and the AI's creative plan.
- **🎬 Cinematic Video Rendering**: Integrates with Google's official **Veo 3.1** (`veo-3.1-generate-preview`) to bring your storyboard to life with high-quality, generated video. 
- **🎵 Custom Audio & Music**: Employs **Lyria 3.5** to compose background music (BGM) that matches the mood and energy of your campaign.
- **🌍 Multilingual Support**: Seamlessly processes prompts in regional languages like Telugu, understanding cultural context for localized marketing.
- **🛡️ Resilient Architecture**: Implements long-running operations polling for heavy video rendering, complete with graceful fallbacks (pre-baked assets) to ensure the UI never hangs if API quotas are exceeded.
- **💅 Premium UI**: Features a sleek, dark-mode cinematic user interface built with raw HTML/CSS/JS.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Werkzeug
- **AI SDK**: `google-genai` (Modern Gemini SDK)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Models Used**: 
  - `gemini-3.1-pro-preview` (Text & Planning)
  - `gemini-3.1-flash-lite-image` (Image Generation)
  - `veo-3.1-generate-preview` (Video Generation)
  - `lyria-3.5` (Music Generation)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.9+**
- A valid **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YourUsername/GDGHYD.git
   cd GDGHYD/campaignflow-lite
   ```

2. **Create a virtual environment** (Recommended):
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # source venv/bin/activate    # On Mac/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your Environment Variables**:
   Set your Gemini API key in your terminal before running:
   ```bash
   # On Windows (PowerShell)
   $env:GEMINI_API_KEY="your_api_key_here"
   
   # On Mac/Linux
   export GEMINI_API_KEY="your_api_key_here"
   ```

5. **Run the Application**:
   ```bash
   python backend/app.py
   ```
   The application will be available at `http://localhost:5000`.

---

## 🎮 How to Use

1. **Start a Campaign**: Enter a product name (e.g., `Zen Coffee Mug` or `గోదావరి పండుగ స్వీట్స్`) and a brief description. Click **Generate Creative Plan**.
2. **Choose a Theme**: Select a visual aesthetic (e.g., Cinematic, Futuristic, Minimal) and click **Apply Theme**.
3. **Upload Asset**: Upload an optional product reference image, or simply click **Skip**.
4. **Generate Storyboard**: Click **Generate Storyboard** to let Gemini Flash Lite Image create your scene visuals.
5. **Render Video**: Click **Render Video**. (Note: Veo video generation takes ~45-60 seconds).
6. **Generate Music**: Click **Generate Music** to synthesize the Lyria backing track.
7. **Final Review**: Click **Load Final Output** to see your completed, AI-generated marketing campaign all in one place!

---

## 🔒 Security & Deployment
This project is configured with a `Procfile` and `requirements.txt`, making it ready for 1-click deployments to platforms like Render, Railway, or Heroku using Gunicorn.

*Note: Never commit your `GEMINI_API_KEY` directly to the codebase.*
