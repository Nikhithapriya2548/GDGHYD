# CampaignFlow Lite API Contract

## Campaign Lifecycle

`POST /api/campaign/create`
*   **Request**: `(TBD - likely product/campaign details)`
*   **Response**: `{ campaign_id, creative_plan: { creative_direction, visual_style, recommended_theme, scene_descriptions: [scene1, scene2], music_mood } }`

`POST /api/campaign/<id>/theme`
*   **Request**: `(TBD - theme preferences)`
*   **Response**: `{ status, theme }`

`POST /api/campaign/<id>/upload`
*   **Request**: `(Multipart form data / file)`
*   **Response**: `{ asset_path, status }`

`POST /api/campaign/<id>/storyboard`
*   **Request**: `(TBD - scene adjustments if any)`
*   **Response**: `{ scenes: [{ scene_id, image_url, prompt, source }] }`

## Generation & Status

`POST /api/campaign/<id>/video/start`
*   **Request**: `(Empty or video config)`
*   **Response**: `{ job_id, status }`

`GET /api/campaign/<id>/video/status/<job_id>`
*   **Response**: `{ status, video_url }`

`POST /api/campaign/<id>/music`
*   **Request**: `(Empty or music config)`
*   **Response**: `{ audio_url, mood, status }`

`GET /api/campaign/<id>/final`
*   **Response**: `{ video_url, audio_url, images, theme, mood, status }`
