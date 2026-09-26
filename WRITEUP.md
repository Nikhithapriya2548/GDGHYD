# CampaignFlow Lite: Hyperlocal AI Video Generation

## Architecture
(Draft notes: Detail how we route between Google Gemini 1.5 Pro for the creative direction, Imagen 3 for storyboard generation, Vertex AI Veo for video, and Lyria for audio. Mention the Flask backend and the async job structure for video generation.)

## Differentiation
While tools like PixVerse, VEED, and Creatify exist, they are generalized global tools. CampaignFlow Lite is positioned explicitly as **Telugu-first** and **hyperlocal**. We natively detect Telugu prompts and automatically enrich generative instructions with culturally relevant lighting, festive details, and South Indian instrumentation (like mridangam and flute) without requiring the user to become a prompt engineer.

## Honest Disclosure
In the interest of transparency for the Kaggle submission: Our application showcases the live conversational flow and API structure designed for real Vertex AI models. Due to API key constraints/timeouts during the hackathon, some of the final outputs (specifically the 4 variations in the conversational editor) rely on pre-baked generative assets. However, the exact API request shapes and routing logic have been accurately modeled and integrated.

## Technical Challenges
(To be filled in after Sync 2 and end-to-end testing)
